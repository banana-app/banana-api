import unittest

from banana.movies.model import *

from funcy import lmap
from whatever import _


class MovieModelsTest(unittest.TestCase):

    def test_genre_transient_copy(self):
        genre = Genre(genre_id=1234,name="Drama")
        lmap(_.transient_copy, [genre])
        self.assertEqual(genre, genre.transient_copy())

    def test_movie_transient_copy(self):
        genre = Genre(genre_id=1234, name="Drama")
        movie = Movie(title='Monty Python',
                      release_year=1979,
                      plot='awesome',
                      external_id=123456,
                      source='tmdb',
                      rating='9.9',
                      poster='some awesome poster')

        movie.genres += [genre]

        self.assertEqual(movie, movie.transient_copy())
