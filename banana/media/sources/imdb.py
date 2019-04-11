from typing import List, Tuple
import imdb

import banana.media.sources.imdbsuggestions as imdbsuggestions
from banana.core import getLogger
from banana.movies.model import MovieMatchCandidate, Genre

logger = getLogger(__name__)


def _imdb_get_poster_if_available(suggestion):
    """
    Extracts poster URL from suggestions, if available. Note that suggestion can have, none, single or list of posters.
    This method just extracts first one, if available.

    :param suggestion: a suggestion for extract poster url from
    :return: poster url or None
    """
    if not suggestion.get("i") or len(suggestion.get("i")) < 1:
        return None
    else:
        return suggestion.get("i")[0]


def _imdb_suggestion_to_search_result(suggestion):
    """
    Maps and IMDB suggestions to search title results. The minimal yet useful set of information, banana
    can use for search.

    :param suggestion: a IMDB suggestion
    :return: Mapped search struct
    """
    return {
        "title": suggestion.get("l"),
        "release_year": suggestion.get("y"),
        "poster": _imdb_get_poster_if_available(suggestion),
        "plot": None,
        "source": "imdb",
        "source_id": suggestion["id"].replace("tt", "")
    }


def _imdb_parse_akas(m):
    """
    Parses IMDB list of akas (alternative titles for a movie). This is little bit messy, at it's just
    scrapped IMDB page with a lot of garbage. This mapping tries to make sens of it.

    :param m: an IMDB movie object
    :return: list of akas (array of alternative names)
    """
    if not m:
        return []
    else:
        original_akas = m.get('akas', [])
        if len(original_akas) > 0:
            ak = [a.strip() for a in original_akas[0].split("\n") if
                  a.strip() != "" and (a[:1] != "(" and a[-1:] != ")")]
            return ak
        else:
            return []


def _imdb_plot(m):
    """
    Extracts plot from IMDB movie entry. This generally my be either:
    * None
    * a string (single plot)
    * a list of plot outlines

    :param m: a IMDB Movie
    :return: a Plot for IMDB movie
    """
    # noinspection PyBroadException
    try:
        plot = m['plot outline']
        if not plot:
            return None
        elif isinstance(plot, str):
            return plot
        elif isinstance(plot, (frozenset, list, set)):
            return plot[0]
        else:
            return plot
    except BaseException:
        logger.debug("Error extracting plot for {}".format(m['title']))
        return None


def _imdb_genres(m):
    """
    Maps IMDB genres to banana Genres. Again like with everything in this API, genres may actually be
    * None
    * a list of genre names

    :param m: a IMDB movie object
    :return: a list of IMDB genres
    """
    # noinspection PyBroadException
    try:
        genres = m.get('genres')
        if not genres:
            return []
        else:
            return [Genre(name=g) for g in genres]
    except BaseException:
        logger.debug("Error extracting genres for {}".format(m['title']))
        return []


def _imdb_to_match_candidate(m: dict) -> MovieMatchCandidate:
    """
    Maps source specific data to general movie match candidate. We use this structure later in banana.
    :param m: a dict containing movie result from IMDB
    :return: a MovieMatchCandidate
    """
    return MovieMatchCandidate(
        title=m.get("title"),
        plot=_imdb_plot(m),
        poster=m.get("cover"),
        original_title=m.get("title"),
        rating=m.get("rating"),
        release_year=m.get("year"),
        external_id=str(m.movieID),
        source="imdb",
        akas=_imdb_parse_akas(m),
        genres=_imdb_genres(m)
    )


class IMDBApi(object):

    @staticmethod
    def match(title) -> List[MovieMatchCandidate]:
        """
        Returns a match candidates for a given movie. This is different from search function, as search uses
        fast but limited information form suggestions API, while this uses slower but richer PyIMDB API.

        :param title - a title to find matching movies in IMDB
        :return: a list of MovieMatchCandidates
        """
        ia = imdb.IMDb()
        movies = ia.search_movie(title)
        for m in movies:
            ia.update(m, 'main')
        return [_imdb_to_match_candidate(m) for m in movies]

    @staticmethod
    def get_by_id(imdb_id: str) -> MovieMatchCandidate:
        """
        Gets a MovieMatchCandidate for a given IMDB id. Note that this id should be numeric part of tmdbid:

        For tt0012345 it should be 0012345

        :return: a MovieMatchCandidate for this ID.
        """
        ia = imdb.IMDb()
        movie = ia.get_movie(str(imdb_id))
        return _imdb_to_match_candidate(movie)

    @staticmethod
    def search(title) -> dict:
        # noinspection PyBroadException
        try:
            suggestions = imdbsuggestions.suggest_movie(title)
            return {'total_results': len(suggestions),
                    'results': [_imdb_suggestion_to_search_result(s) for s in suggestions]}
        except BaseException:
            return {'total_results': 0, 'results': []}

