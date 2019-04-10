import rx
from funcy import any
from whatever import _

from banana.core import JobContext, getLogger
from banana.media.item import ParsedMediaItem
from banana.media.sources import get_media_source
from banana.movies.model import MovieMatchRequest


class FixMatchObservable:
    """
    This observable handles fix match request from UI (meaning that user manually chooses a movie candidate to fix match
    of a ParsedMediaItem). MovieMatchRequest input carries all required information:

    See [ManualMatchingObservable] for all details.
    """

    def __init__(self,
                 job_context: JobContext,
                 media_id: int,
                 match_request: MovieMatchRequest,
                 source_factory=get_media_source):
        super().__init__()
        self._media_id = media_id
        self._job_context = job_context
        self.logger = getLogger(self.__class__.__name__)
        self._match_request = match_request
        self._get_media_source = source_factory

    def __call__(self, observer: rx.Observer):
        """
        It emits an event to the observers with ParsedMediaItem and movie match candidate to fix match for that item.
        :param observer - an Observer to fix match.
        """
        try:
            if any(_ == self._match_request.match_type, ['imdb', 'tmdb', 'local']):
                media_to_fix = ParsedMediaItem.query.filter_by(id=self._media_id).one_or_none()
                candidate = self._get_media_source(self._match_request.match_type).get_by_id(
                    self._match_request.match_type_id)

                observer.on_next((media_to_fix, candidate))
                observer.on_completed()

            else:
                observer.on_error(f'Unknown fix match request type: {self._match_request}')

        except BaseException as e:
            observer.on_error(e)
