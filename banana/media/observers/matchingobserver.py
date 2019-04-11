import traceback
from typing import Tuple

import rx
from funcy import none
from whatever import _

from banana.core import Config, socket as web_socket
from banana.core import db, getLogger
from banana.core.jobs import JobContext
from banana.media.item import ParsedMediaItem
from banana.media.model import UnmatchedItem
from banana.media.observers import EmitEventMixin, JobErrorEvent
from banana.media.targets import get_media_target_resolver, MediaTargetResolver
from banana.movies.commands import match_movie
from banana.movies.matchdecider import MatchType, MatchDecider
from banana.movies.matcher import get_matcher, Matcher
from banana.movies.model import MovieMatchCandidate, Movie


class MediaItemMatchingObserver(rx.Observer):

    def __init__(self,
                 job_context: JobContext,
                 resolver: MediaTargetResolver = get_media_target_resolver(Config.media_target_resolver()),
                 matcher: Matcher = get_matcher(Config.media_matcher()),
                 decider: MatchDecider = MatchDecider()
                 ):
        self._job_context = job_context
        self.matcher = matcher
        self.decider = decider
        self.resolver = resolver
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, index_and_media: Tuple[int, ParsedMediaItem]):
        # noinspection PyBroadException
        try:

            # check if this item is not yet matched
            _, media = index_and_media
            media.job_id = self._job_context.id()

            if not media.is_movie():
                self.logger.info("{} not a movie. Skipping.".format(media.filename))
                return

            already_matched = media.already_matched()

            if already_matched:
                self.logger.info("Media item {} already matched to {}. Skipping.".format(
                    already_matched.absolute_path(), already_matched.absolute_target_path()))
                return

            match_result = self.decider.try_match(self.matcher.top5_matches(media))

            if match_result.match_type() is MatchType.MATCHED:
                matched_movie = match_result.matched_movie()

                # try to find if we have this movie already

                target_media, target = self.resolver.resolve(media=media, movie=matched_movie)

                if not target.can_link():
                    return

                match_movie(media=target_media,
                            movie=matched_movie,
                            target=target)

            else:
                ui = UnmatchedItem(parsed_media_item=media,
                                   potential_matches=match_result.potential_matches(),
                                   non_match_reason=match_result.reason())

                db.session.add(ui)

            db.session.commit()

        except BaseException:
            self.logger.warning("Exception caught while processing media item: {}"
                                .format(traceback.format_exc()))
            db.session.rollback()

    def on_completed(self):
        pass

    def on_error(self, error):
        self.logger.warn("Matching observer caught exception: {}".format(traceback.format_exc()))


class ManualMediaItemMatchingObserver(EmitEventMixin, rx.Observer):

    def __init__(self,
                 job_context: JobContext,
                 resolver: MediaTargetResolver = get_media_target_resolver(Config.media_target_resolver()),
                 web_socket = web_socket):
        super().__init__()
        self._job_context = job_context
        self._web_socket = web_socket
        self.resolver = resolver
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, media_and_movie: Tuple[UnmatchedItem, MovieMatchCandidate]):
        # noinspection PyBroadException
        try:
            unmatched, candidate = media_and_movie
            media = unmatched.parsed_media_item.transient_copy()
            media.job_id = self._job_context.id()
            movie = candidate.to_movie()
            target_media, target = self.resolver.resolve(media=media, movie=movie)

            match_movie(media=target_media, movie=movie, target=target)

            db.session.delete(unmatched)
            db.session.commit()

        except BaseException as e:
            self.logger.warning("Exception caught while processing media item: {}. Emitting JobErrorEvent and"
                                " unwinding gracefully. This media item would not be processed."
                                .format(traceback.format_exc()))
            db.session.rollback()

            # We need to handle this gracefully. Exceptions emitted from Observers means that Observable will
            # unsubscribe all of them, and in fact this will be rethrown. We want, however to emit proper
            # event to UI first, the we rethrow to finish job

            self.emit(self._web_socket, JobErrorEvent(job_id=self._job_context.id(),
                                                      job_type=self._job_context.type(),
                                                      cause=str(e)))
            raise e

    def on_completed(self):
        pass

    def on_error(self, error):
        self.logger.warning('ManualMediaItemMatchingObserver on_error: {}'.format(error))


class FixMatchObserver(EmitEventMixin, rx.Observer):

    def __init__(self,
                 job_context: JobContext,
                 resolver: MediaTargetResolver = get_media_target_resolver(Config.media_target_resolver()),
                 web_socket = web_socket):
        super().__init__()
        self._job_context = job_context
        self._web_socket = web_socket
        self.resolver = resolver
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, media_and_candidate: Tuple[ParsedMediaItem, MovieMatchCandidate]):
        # noinspection PyBroadException
        try:
            source_media, candidate = media_and_candidate
            source_media.job_id = self._job_context.id()
            movie = candidate.to_movie()
            target_media, target = self.resolver.resolve(media=source_media.transient_copy(), movie=movie)

            already_existing_movie = Movie.query.filter_by(external_id=movie.external_id).first()
            if not already_existing_movie:
                movie.media_items = [target_media]
                db.session.add(movie)
            else:
                already_existing_movie.media_items += [target_media]

            target.do_relink(source_media.absolute_target_path())
            source_movie = source_media.matched_movie

            # if we are unlinking the only linke media from movie, we remove whole
            # movie altogether
            if source_movie and none(_.id != source_media.id, source_movie.media_items):
                db.session.delete(source_movie)

            db.session.delete(source_media)
            db.session.commit()

        except BaseException as e:
            self.logger.warning("Exception caught while processing media item: {}. Emitting JobErrorEvent and"
                                " unwinding gracefully. This media item would not be processed."
                                .format(traceback.format_exc()))
            db.session.rollback()

            # We need to handle this gracefully. Exceptions emitted from Observers means that Observable will
            # unsubscribe all of them, and in fact this will be rethrown. We want, however to emit proper
            # event to UI first, the we rethrow to finish job

            self.emit(self._web_socket, JobErrorEvent(job_id=self._job_context.id(),
                                                      job_type=self._job_context.type(),
                                                      cause=str(e)))
            raise e

    def on_completed(self):
        pass

    def on_error(self, error):
        self.logger.warning('ManualMediaItemMatchingObserver on_error: {}'.format(error))
