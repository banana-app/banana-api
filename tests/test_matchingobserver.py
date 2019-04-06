import unittest

from banana.core import app, db
from unittest.mock import MagicMock
from banana.movies.model import *
from banana.media.model import UnmatchedItem
from banana.media.item import ParsedMediaItem

from banana.media.observers import MediaItemMatchingObserver
from banana.movies.matcher import SourceMatcher
from banana.media.sources import TMDBApi
from banana.media.targets import SkipExistingMediaTargetResolver, NoOpMediaTargetBuilder

from tests import MockJobContext


class MediaItemMatchingObserverTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
        self.db = db
        self.db.drop_all()
        self.db.create_all()

    def test_perfect_match(self):
        item = ParsedMediaItem(title="The Goat", year="2015", filename="The Goat 2015.mp4", path="c:/movies")
        source = TMDBApi()
        source.match = MagicMock(return_value=[MovieMatchCandidate(title="The Goat", release_year=2015)])

        media_matching_observer = MediaItemMatchingObserver(job_context=MockJobContext(),
                                                            matcher=SourceMatcher(source=source),
                                                            resolver=SkipExistingMediaTargetResolver(
                                                                media_target_builder=NoOpMediaTargetBuilder()
                                                            ))
        media_matching_observer.on_next(index_and_media=(1,item))

        matched_movie = Movie.query.filter(Movie.title == 'The Goat').first()
        matched_movies_count = Movie.query.filter(Movie.title == 'The Goat').count()

        self.assertIsNotNone(matched_movie)
        self.assertEqual('The Goat', matched_movie.title)
        self.assertEqual(2015, matched_movie.release_year)
        self.assertEqual(1, matched_movies_count)

    def test_unmached_item(self):
        item = ParsedMediaItem(title="The Goat", year="2015", filename="The Goat 2015.mp4", path="c:/movies")
        source = TMDBApi()
        source.match = MagicMock(return_value=[MovieMatchCandidate(title="Will Never Match", release_year=1959)])

        media_matching_observer = MediaItemMatchingObserver(job_context=MockJobContext(),
                                                            matcher=SourceMatcher(source=source),
                                                            resolver=SkipExistingMediaTargetResolver(
                                                                media_target_builder=NoOpMediaTargetBuilder()
                                                            ))
        media_matching_observer.on_next(index_and_media=(1,item))

        unmatched_item = UnmatchedItem.query.join(ParsedMediaItem) \
            .filter(ParsedMediaItem.title == 'The Goat').first()

        movies_count = Movie.query.count()

        self.assertIsNotNone(unmatched_item)
        self.assertEqual('2015', unmatched_item.parsed_media_item.year)
        self.assertEqual(0, movies_count)
