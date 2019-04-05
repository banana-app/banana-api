from banana.core import db

from ..media.item import ParsedMediaItem
from ..movies.model import Movie
from ..media.targets import MediaTarget


def match_movie(media: ParsedMediaItem, movie: Movie, target: MediaTarget) -> Movie:
    """
    Executes movie match. If movie already exists, it connects media item to it;
    otherwise creates new movie entry and links media item to it.

    Links movie to the target using supplied media target.
    """
    result = None
    already_existing_movie = Movie.query.filter_by(external_id=movie.external_id).first()
    if not already_existing_movie:
        movie.media_items = [media]
        db.session.add(movie)
        result = movie
    else:
        already_existing_movie.media_items += [media]
        result = already_existing_movie

    target.do_link()
    db.session.commit()

    return result

