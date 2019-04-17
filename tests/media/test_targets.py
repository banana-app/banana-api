import unittest
from unittest.mock import MagicMock

from banana.media.targets import *
from banana.movies.model import Movie
from banana.media.item import ParsedMediaItem
from banana.media.nameformatter import NameFormatter


class MediaTargetsTest(unittest.TestCase):

    def test_skip_already_existing_media_resolver_for_already_existing_target(self):

        class MockMediaTarget(MediaTarget):

            def can_link(self):
                return True

            def do_link(self):
                pass

            def already_exist(self):
                pass

            def do_relink(self, from_path: str):
                pass

        media_target = MockMediaTarget()
        media_target.already_exist = MagicMock(return_value=True)

        class MockMediaTargetBuilder(MediaTargetBuilder):

            def build(self, media: ParsedMediaItem, movie: Movie, formatter: NameFormatter):
                return media_target

        media = ParsedMediaItem()
        movie = Movie(title='Monty Python', release_year=2015)
        target = SkipExistingMediaTargetResolver(media_target_builder=MockMediaTargetBuilder(),
                                                 formatter=NameFormatter())

        _, media_target = target.resolve(media, movie)

        self.assertEqual(False, media_target.can_link())
        self.assertRaises(NotImplementedError, media_target.do_link)


