from .item import ParsedMediaItem
from ..movies.model import Movie, canonical_movie_title
from ..core import Config
from dataclasses import replace
from jinja2 import Template
import re


class NameFormatter(object):
    """
    This is movie and tv episode name pattern based formatter. Basically it has regular python
    like string format, and the it's fed with both media item (the file) and matched movie data or episode.
    """

    def __init__(self, template: str = Config.media_movie_pattern_name(),
                 movies_target_path=Config.media_movies_target_path()):
        jinja_template = Template(template)
        jinja_template.globals['canonical_movie_title'] = canonical_movie_title
        jinja_template.globals['media_movies_target_path'] = movies_target_path
        self._template = jinja_template

    def format(self, movie: Movie, media: ParsedMediaItem):
        """
        Format name according to template. Remove all characters which are commonly forbidden by filesystems.
        :param movie: movie being fed to the formatter
        :param media: parsed media item being fed to the formatter
        :return: formatted title
        """

        # sanitize movie and media by making transient copies
        # they may already be added to the SQL session, and we want to avoid possible
        # modifications in formatter.
        sanitized_movie = replace(movie.transient_copy(), title=re.sub(r'[\\/*?:"<>|]', '', movie.title))
        return self._template.render(movie=sanitized_movie, file=media.transient_copy())
