from banana.media.nameformatter import NameFormatter
from banana.movies.model import Movie
from banana.media.item import ParsedMediaItem
from dataclasses import replace
from banana.core import Config

import unittest
import pathlib

movie = Movie(title="These Daughters of Mine",
              original_title="Moje Córki Krowy",
              release_year="2015",
              plot="Some plot",
              external_id=4834762,
              rating="6.7",
              poster="https://via.placeholder.com/150",
              genres=[],
              source="imdb")

file = ParsedMediaItem(
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
    title="These Daughters of Mine",
    website="",
    widescreen="",
    year="2015")


class NameFormatterTest(unittest.TestCase):

    def test_canonical_title(self):
        formatted_name = NameFormatter('{{movie.canonical_title()}}').format(movie=movie, media=file)
        self.assertEqual("These Daughters of Mine (2015)", formatted_name)

    def test_canonical_original_title(self):
        formatted_name = NameFormatter('{{canonical_movie_title(movie.original_title, movie.release_year)}}') \
            .format(movie=movie, media=file)
        self.assertEqual("Moje Corki Krowy (2015)", formatted_name)

    def test_quality_and_resolution(self):
        formatted_name = NameFormatter('{{movie.canonical_title()}} - {{file.quality}} - {{file.resolution}}') \
            .format(movie=movie, media=file)
        self.assertEqual("These Daughters of Mine (2015) - BluRay - 1080p", formatted_name)

    def test_missing_properties(self):
        formatted_name = NameFormatter('{{movie.canonical_title()}} - {{file.language}}') \
            .format(movie=movie, media=file)
        self.assertEqual("These Daughters of Mine (2015) - ", formatted_name)

    def test_logic_expressions(self):
        formatted_name = NameFormatter(
            '{{movie.canonical_title()}} - {{file.language if file.language != None}}') \
            .format(movie=movie, media=file)
        formatted_name2 = NameFormatter(
            '{{movie.canonical_title()}}{%if file.quality is not none%} - ({{file.quality}}){%endif%}') \
            .format(movie=movie, media=file)
        self.assertEqual("These Daughters of Mine (2015) - ", formatted_name)
        self.assertEqual("These Daughters of Mine (2015) - (BluRay)", formatted_name2)

    def test_grouping_path(self):
        """
        Lets assume we want to group movies into directories by resolution
        movies/1080p/These Daughters of Mine (2015)/These Daughters of Mine (2015) - BluRay - 1080p.mp4
        """
        formatted_name = NameFormatter('movies/{{file.resolution}}/'
                                       '{{movie.canonical_title()}}/'
                                       '{{movie.canonical_title()}}'
                                       ' - {{file.quality}} - {{file.resolution}}.{{file.container}}')\
            .format(movie=movie, media=file)

        self.assertEqual(
            'movies/1080p/These Daughters of Mine (2015)/These Daughters of Mine (2015) - BluRay - 1080p.mp4',
            formatted_name)

        path = pathlib.PurePath(formatted_name).parts
        self.assertEqual(('movies', '1080p', 'These Daughters of Mine (2015)',
                          'These Daughters of Mine (2015) - BluRay - 1080p.mp4'), path)

    def test_extended_plex_pattern(self):
        formatted_name = NameFormatter(
            "{{movie.canonical_title()}}"
            "{%if file.quality is not none%} - {{file.quality}}{%endif%}"
            "{%if file.resolution is not none%} - {{file.resolution}}{%endif%}.{{file.container}}")\
            .format(movie=movie, media=file)

        self.assertEqual("These Daughters of Mine (2015) - BluRay - 1080p.mp4", formatted_name)

    def test_movie_sanitization(self):
        suspected_title = replace(movie, title="<>:?")
        formatted_name = NameFormatter("{{movie.title}}").format(movie=suspected_title, media=file)

        self.assertEqual('', formatted_name)
        self.assertEqual('<>:?', suspected_title.title)

    def test_movies_target_path(self):
        formatted_name = NameFormatter('{{media_movies_target_path}}/{{movie.canonical_title()}} - {{file.quality}} '
                                       '- {{file.resolution}}') \
            .format(movie=movie, media=file)
        self.assertEqual("{}/These Daughters of Mine (2015) - BluRay - 1080p".format(Config.media_movies_target_path()),
                         formatted_name)
