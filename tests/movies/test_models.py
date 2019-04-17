import unittest

from banana.media.model import UnmatchedItem
from banana.movies.matchdecider import NonMatchReason
from banana.movies.model import *

from funcy import lmap
from whatever import _


class MovieModelsTest(unittest.TestCase):

    def setUp(self) -> None:
        self.genre = Genre(genre_id=1234,name="Drama")
        self.movie = Movie(title='Monty Python',
                           release_year=1979,
                           plot='awesome',
                           external_id='123456',
                           source='tmdb',
                           rating='9.9',
                           poster='some awesome poster')
        self.media = ParsedMediaItem(id=1, filename='Monthy Python 1969.mp4', title='Monthy Python', year='1969')
        self.candidate = MovieMatchCandidate(title='The Rock',
                                             release_year=2012,
                                             plot='kewl',
                                             external_id='345',
                                             source='imdb',
                                             rating='3.3')

    def test_genre_transient_copy(self):
        genre = Genre(genre_id=1234,name="Drama")
        lmap(_.transient_copy, [genre])
        self.assertEqual(genre, genre.transient_copy())

    def test_movie_transient_copy(self):
        genre = Genre(genre_id=1234, name="Drama")
        movie = Movie(title='Monty Python',
                      release_year=1979,
                      plot='awesome',
                      external_id='123456',
                      source='tmdb',
                      rating='9.9',
                      poster='some awesome poster')

        movie.genres += [genre]

        self.assertEqual(movie, movie.transient_copy())

    def test_unmatched_serialization_deserialization(self):

        movie, candidate, genre, media = self.movie, self.candidate, self.genre, self.media

        unmatched = UnmatchedItem(potential_matches=[candidate, candidate],
                                  parsed_media_item=media,
                                  non_match_reason=NonMatchReason.LOW_TRESHOLD)

        serialized = unmatched.to_json()

        deserialized = UnmatchedItem.from_json(serialized)

        serialized_many = unmatched.schema().dumps([unmatched, unmatched], many=True)
        deserialized_many = UnmatchedItem.from_json(serialized_many, many=True)

        self.assertEqual(unmatched, deserialized)
        self.assertEqual(deserialized_many, [unmatched, unmatched])

    def test_media_serialization_deserialization(self):

        media = self.media

        serialized = media.to_json()
        deserialized = ParsedMediaItem.from_json(serialized)
        serialized_many = ParsedMediaItem.schema().dumps([media, media], many=True)
        deserialized_many = ParsedMediaItem.from_json(serialized_many, many=True)

        self.assertEqual(deserialized, media)
        self.assertEqual(deserialized_many, [media, media])

    def test_movie_serialization_deserialization(self):

        movie = self.movie

        serialized = movie.to_json()
        deserialized = Movie.from_json(serialized)

        print(movie)
        print(deserialized)

        serialized_many = Movie.schema().dumps([movie, movie], many=True)
        deserialized_many = Movie.from_json(serialized_many, many=True)

        self.assertEquals(movie, deserialized)
        self.assertEquals(deserialized_many, [movie, movie])
