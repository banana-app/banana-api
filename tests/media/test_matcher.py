import unittest
from unittest.mock import MagicMock
from dataclasses import replace

from banana.media.sources import TMDBApi, IMDBApi
from banana.movies.model import Movie, MovieMatchCandidate
from banana.media.item import ParsedMediaItem
from banana.movies.matcher import SourceMatcher, FallbackSourceMatcher, FallbackLowThresholdSourceMatcher, \
    _boost_match_ratio_for_closest_release_year


class MatcherTest(unittest.TestCase):

    def setUp(self):
        self.movie_match_candidate = MovieMatchCandidate(title="These Daughters of Mine",
                                                         original_title="Moje Córki Krowy",
                                                         release_year=2015,
                                                         plot="Some plot",
                                                         external_id=4834762,
                                                         rating="6.7",
                                                         poster="https://via.placeholder.com/150",
                                                         genres=[],
                                                         source="tmdb")

        self.movie = Movie(title="These Daughters of Mine",
                           original_title="Moje Córki Krowy",
                           release_year="2015",
                           plot="Some plot",
                           external_id=4834762,
                           rating="6.7",
                           poster="https://via.placeholder.com/150",
                           genres=[],
                           source="imdb")

        self.file = ParsedMediaItem(
            filename="These Daughters of Mine 2015 1080p BluRay DD5.1.mp4",
            path="some path",
            audio="DD5.1",
            codec="x264",
            container="mp4",
            episode="",
            episodeName="",
            garbage="",
            group="",
            hardcoded="",
            language="",
            proper="",
            quality="BluRay",
            region="",
            repack="",
            resolution="1080p",
            season="",
            title="THESE daughters of MINE",
            website="",
            widescreen="",
            year=2015)

    def test_matched_is_case_insesnsitive(self):
        tmdb_source = TMDBApi()
        tmdb_source.match = MagicMock(return_value=[self.movie_match_candidate])
        matches = SourceMatcher(tmdb_source).top5_matches(self.file)

        tmdb_source.match.assert_called_with(title='THESE daughters of MINE')
        self.assertEqual(1, len(matches))
        self.assertEqual(100, matches[0].match)

    def test_match_against_original_title(self):
        tmdb_source = TMDBApi()
        file_with_original_title = replace(self.file, title="Moje Córki Krowy")
        tmdb_source.match = MagicMock(return_value=[self.movie_match_candidate])
        matches = SourceMatcher(tmdb_source).top5_matches(file_with_original_title)

        tmdb_source.match.assert_called_with(title='Moje Córki Krowy')
        self.assertEqual(100, matches[0].match)

    def test_match_against_akas(self):
        tmdb_source = TMDBApi()
        file_with_foereign_title = replace(self.file, title="Mine døtre kuene")
        self.movie_match_candidate.akas = ["Foo", "bar", "Mine døtre kuene"]
        tmdb_source.match = MagicMock(return_value=[self.movie_match_candidate])
        matches = SourceMatcher(tmdb_source).top5_matches(file_with_foereign_title)

        tmdb_source.match.assert_called_with(title='Mine døtre kuene')
        self.assertEqual(100, matches[0].match)

    def test_fallback_matcher(self):
        tmdb_source = TMDBApi()
        tmdb_source.match = MagicMock(return_value=[])
        imdb_source = IMDBApi()
        imdb_source.match = MagicMock(return_value=[self.movie_match_candidate])

        matcher = FallbackSourceMatcher(primary=tmdb_source, secondary=imdb_source)
        matches = matcher.top5_matches(self.file)

        tmdb_source.match.assert_called_with(title='THESE daughters of MINE')
        imdb_source.match.assert_called_with(title='THESE daughters of MINE')

        self.assertEqual(1, len(matches))
        self.assertEqual(100, matches[0].match)

    def test_low_threshold_fallback_matcher_with_dedupliaction(self):
        tmdb_source = TMDBApi()
        tmdb_source.match = MagicMock(return_value=[replace(self.movie_match_candidate,
                                                            title="DO NOT MATCH",
                                                            original_title="DO NOT MATCH", external_id=123456)])
        tmdb_source.get_by_imdbid_id = MagicMock(return_value=replace(self.movie_match_candidate,
                                                                       external_id=123456))
        imdb_source = IMDBApi()
        imdb_source.match = MagicMock(return_value=[self.movie_match_candidate])

        matcher = FallbackLowThresholdSourceMatcher(primary=tmdb_source, secondary=imdb_source)
        matches = matcher.top5_matches(self.file)

        self.assertEqual(1, len(matches))
        self.assertEqual(100, matches[0].match)
        tmdb_source.match.assert_called_with(title='THESE daughters of MINE')
        tmdb_source.get_by_imdbid_id.assert_called_with(4834762)
        imdb_source.match.assert_called_with(title='THESE daughters of MINE')

    def test_low_threshold_fallback_matcher_no_dedupliaction(self):
        tmdb_source = TMDBApi()
        tmdb_source.match = MagicMock(return_value=[replace(self.movie_match_candidate,
                                                            title="DO NOT MATCH",
                                                            original_title="DO NOT MATCH", external_id=123456)])
        tmdb_source.get_by_imdbid_id = MagicMock(return_value=replace(self.movie_match_candidate,
                                                                      external_id=234567))
        imdb_source = IMDBApi()
        imdb_source.match = MagicMock(return_value=[self.movie_match_candidate])

        matcher = FallbackLowThresholdSourceMatcher(primary=tmdb_source, secondary=imdb_source)
        matches = matcher.top5_matches(self.file)

        self.assertEqual(2, len(matches))
        self.assertEqual(100, matches[0].match)
        tmdb_source.match.assert_called_with(title='THESE daughters of MINE')
        tmdb_source.get_by_imdbid_id.assert_called_with(4834762)
        imdb_source.match.assert_called_with(title='THESE daughters of MINE')

    def test_boost_ratio(self):
        movies = [replace(self.movie_match_candidate, release_year=2013, match=95),
                  replace(self.movie_match_candidate, release_year=2012, match=95),
                  replace(self.movie_match_candidate, release_year=2010, match=95)]

        movies_with_boosted_ratio = _boost_match_ratio_for_closest_release_year(movies, candidate_year=2014)

        self.assertEqual(3, len(movies_with_boosted_ratio))
        self.assertEqual(95, movies_with_boosted_ratio[0].match)
        self.assertEqual(94, movies_with_boosted_ratio[1].match)
        self.assertEqual(94, movies_with_boosted_ratio[2].match)

    def test_low_threshold_fallback_matcher_with_boost(self):
        tmdb_source = TMDBApi()
        tmdb_source.match = MagicMock(return_value=[
            replace(self.movie_match_candidate),
            replace(self.movie_match_candidate, release_year=2012),
            replace(self.movie_match_candidate, release_year=2011)])

        imdb_source = IMDBApi()
        imdb_source.match = MagicMock(return_value=[])

        matcher = FallbackLowThresholdSourceMatcher(primary=tmdb_source, secondary=imdb_source)
        matches = matcher.top5_matches(replace(self.file, year=2014))

        self.assertEqual(3, len(matches))
        self.assertEqual(97, matches[0].match)
        self.assertEqual(96, matches[1].match)
        self.assertEqual(96, matches[2].match)
