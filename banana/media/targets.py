from abc import ABC, abstractmethod
import os
from banana.media.item import ParsedMediaItem
from banana.media.nameformatter import NameFormatter
from banana.movies.model import Movie
from banana.core import Config, getLogger

logger = getLogger(__name__)


class MediaTarget(ABC):
    """
    Base class for all MediaTargets.
    """

    @abstractmethod
    def do_link(self):
        """
        Links two media items on filesystem source and target. Linking process may be anything: actually creating
        and filesystem link, a local copy or even transferring data from remote filesystem.

        Both source and target attributes depends on specific implementations. Those may be a path-like stings or even
        URI. It is up to implementing class to interpr them.

        :param source: a source media item
        :param target: a target
        """
        pass

    def already_exist(self) -> bool:
        """
        Check if given target already exist. This, again, may be anything: a local file copy, or a link, or a copy of
        a remote file.

        :param target: Check if target already exit
        :return: True if target already exist, false otherwise
        """
        pass

    @abstractmethod
    def can_link(self) -> bool:
        pass


class MediaTargetBuilder(ABC):

    @abstractmethod
    def build(self, media: ParsedMediaItem, movie: Movie, formatter: NameFormatter) -> MediaTarget:
        pass


class MediaTargetResolver(ABC):

    @abstractmethod
    def resolve(self, media: ParsedMediaItem, movie: Movie) -> (ParsedMediaItem, MediaTarget):
        pass


class SkipExistingMediaTargetResolver(MediaTargetResolver):
    """
    This resolver will resolve to Media Target which would not link if target file exists.
    """

    def __init__(self, media_target_builder: MediaTargetBuilder, formatter: NameFormatter = NameFormatter()):
        self._media_target_builder = media_target_builder
        self._formatter = formatter
        self.logger = getLogger(__class__.__name__)

    def resolve(self, media: ParsedMediaItem, movie: Movie) -> (ParsedMediaItem, MediaTarget):
        media_target = self._media_target_builder.build(media=media, movie=movie, formatter=self._formatter)
        target_absolute_path = self._formatter.format(movie, media)

        if media_target.already_exist():
            self.logger.info('Target file {} for a {} already exist. Skipping.'.format(
                target_absolute_path, media.absolute_path()))

            class DoNotTouchMediaTarget(MediaTarget):

                def can_link(self):
                    return False

                def already_exist(self):
                    return True

                def do_link(self):
                    raise NotImplementedError('This is a DoNotTouchMediaTarget. Target media {} already '
                                              'exist and cannot be linked to {}'.format(target_absolute_path,
                                                                                        media.absolute_path()))

            return media, DoNotTouchMediaTarget()
        else:
            media.set_target_absolute_path(target_absolute_path)
            return media, media_target


class NoOpMediaTargetBuilder(MediaTargetBuilder):

    def build(self, media: ParsedMediaItem, movie: Movie, formatter: NameFormatter):

        class NoOpMediaTarget(MediaTarget):
            """
            No op media target for dry runs. Just logs information to the logs file.
            """

            def __init__(self, _media: ParsedMediaItem, _movie: Movie, _formatter: NameFormatter):
                self._media = _media
                self._movie = _movie
                self._formatter = _formatter

            def do_link(self):
                logger.info("**Dry Run** Just logging information. Linking {} to {}".format(
                    self._media.absolute_path(),
                    self._formatter.format(self._movie, self._media)))

            def already_exist(self) -> bool:
                return False

            def can_link(self) -> bool:
                return True

        return NoOpMediaTarget(_media=media, _movie=movie, _formatter=formatter)


class HardLinkMediaTargetBuilder(MediaTargetBuilder):

    def build(self, media: ParsedMediaItem, movie: Movie, formatter: NameFormatter):
        class HardLinkMediaTarget(MediaTarget):

            def __init__(self, media: ParsedMediaItem, movie: Movie, formatter: NameFormatter):
                self._media = media
                self._movie = movie
                self._formatter = formatter

            def do_link(self):
                """
                Media Target strategy that links (hard link on Unices and JointPoint on Windows). We assume that in this case,
                both source and target are path-like structures.

                :param source: source media file
                :param target: a hard link name
                """
                source = self._media.absolute_path()
                target = self._formatter.format(self._movie, self._media)
                logger.info("Creating hard link from {} to {}".format(source, target))
                target_dirname = os.path.dirname(target)
                os.makedirs(target_dirname, exist_ok=True)
                os.link(source, target)

            def already_exist(self) -> bool:
                """
                Check if a target, the link name already exist on the filesystem.
                :param target: a link name we are going to create
                :return: True - if file already exist, False otherwise
                """
                return os.path.isfile(self._formatter.format(movie=self._movie, media=self._media))

            def can_link(self):
                return not self.already_exist()

        return HardLinkMediaTarget(media=media, movie=movie, formatter=formatter)


_media_targets = {
    "noop": NoOpMediaTargetBuilder(),
    "hardlink": HardLinkMediaTargetBuilder()
}


def get_media_target_builder(target: str) -> MediaTargetBuilder:
    return _media_targets[target]


_media_target_resolvers = {
    "skip_existing": SkipExistingMediaTargetResolver(
        media_target_builder=get_media_target_builder(Config.media_target())
    )
}


def get_media_target_resolver(resolver: str) -> MediaTargetResolver:
    return _media_target_resolvers[resolver]
