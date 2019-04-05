import tmdbsimple as tmdb
import textwrap
from datetime import datetime
from banana.core import tbdb_api_key
from typing import List
from banana.movies.model import MovieMatchCandidate, Genre
from cachetools.func import ttl_cache

from logging import getLogger

logger = getLogger(__name__)

tmdb.API_KEY = tbdb_api_key()


def tmdb_date_to_date(d):
    if not d:
        return None
    try:
        return datetime.strptime(d, "%Y-%M-%d")
    except ValueError as e:
        logger.warn("Exception caught while converting date, {}".format(e))
        return None


class TMDBApi:

    @staticmethod
    @ttl_cache(ttl=60 * 60 * 600)
    def get_genres():
        return tmdb.Genres().movie_list()["genres"]
    
    def _find_genre_name_by_id(genre_id: int) -> str:
        genres = TMDBApi.get_genres()
        return next(g['name'] for g in genres if g['id'] == genre_id)

    def _tmdb_genres(genre_ids):
        return [Genre(name=TMDBApi._find_genre_name_by_id(gid), genre_id=gid) for gid in genre_ids]     

    @staticmethod
    def _tmdb_poster_url(tmdb_poster_path: str) -> str:
        if not tmdb_poster_path:
            return None
        else:
            return "https://image.tmdb.org/t/p/w600_and_h900_bestv2/" + tmdb_poster_path

    @staticmethod
    def _tmdb_release_year(tmdb_date: str) -> int:
        date = tmdb_date_to_date(tmdb_date)
        if not date:
            return None
        else:
            return date.year
     
    @staticmethod
    def _tmdb_plot(overview: str) -> str:
        if not overview:
            return None
        else:
            return textwrap.shorten(overview, width=200, placeholder="...")

    @staticmethod
    def _tmdb_to_movie_search_item(tmdb_search_result: dict) -> dict:
        result = {
            "title": tmdb_search_result.get("title"),
            "original_title": tmdb_search_result.get("original_title"),
            "poster": TMDBApi._tmdb_poster_url(tmdb_search_result.get("poster_path")),
            "plot": TMDBApi._tmdb_plot(tmdb_search_result.get("overview")),
            "release_year": TMDBApi._tmdb_release_year(tmdb_search_result.get("release_date")),
            "source_id": tmdb_search_result.get("id"),
            "source": "tmdb"
        }
        return result

    @staticmethod
    def _tmdb_to_movie_match_candidate(m, akas=None, prefetch_genres=True) -> MovieMatchCandidate:
        genres = []

        # For search results wo do only have genre_ids, so we need to prefetch them;
        # for full movie info, we already have all information we need
        if prefetch_genres:
            genres = TMDBApi._tmdb_genres(m.get("genre_ids", []))
        else:
            original_genres = m.get("genre_ids", [])
            genres = [Genre(genre_id=g) for g in original_genres]
        
        mc = MovieMatchCandidate(title=m.get("title"), 
            original_title=m.get("original_title"),
            release_year=TMDBApi._tmdb_release_year(m.get("release_date")),
            plot=m.get("overview"),
            match=m.get("match"),
            external_id=str(m.get("id")),
            rating=m.get("vote_average"),
            akas=akas,
            poster=TMDBApi._tmdb_poster_url(m.get("poster_path")),
            genres=genres,
            source="tmdb"
            )
        
        return mc
        
    @staticmethod
    def movie_top3_cast(tmdb_id):
        movie = tmdb.Movies(tmdb_id).info(append_to_response=['credits'])
        cast = movie.get("credits").get("cast")[:3]
        result = []

        for c in cast:
            result.append({
                "profile_picture" : TMDBApi._tmdb_poster_url(c.get("profile_path")),
                "character" : c.get("character"),
                "name": c.get("name"),
                "id": c.get("id"),
                "source": "tmdb"
            })
        
        return result

    # Fast search for UI search functionality; it should return only minimal set of information as a dict 
    @staticmethod
    def match(title: str) -> List[MovieMatchCandidate]:
        results = tmdb.Search().movie(query=title)['results']
        matches = []
        for m in results:
            akas = tmdb.Movies(m["id"]).alternative_titles()['titles']
            akas = [a['title'] for a in akas]
            matches.append(TMDBApi._tmdb_to_movie_match_candidate(m, akas))
        logger.debug("IMDB matches {}".format(matches))
        return matches

    # Returns possible match candidates for a movie; this is much slower than search, as it returns a richer
    # set of information
    @staticmethod
    def search(title: str):
        results = tmdb.Search().movie(query=title)['results']
        return [TMDBApi._tmdb_to_movie_search_item(m) for m in results]

    @staticmethod
    def get_by_imdbid_id(imdbid) -> MovieMatchCandidate:
        try:
            results = tmdb.Find("tt" + str(imdbid)).info(external_source="imdb_id")['movie_results']
            logger.debug("Getting TMDB movie candidates by IMDB: {}. Resuls: {}".format(imdbid, results))
            if len(results) == 0:
                return None
            # Assume we don't have duplicated entries in TMDB and only one movie per imdb
            return TMDBApi._tmdb_to_movie_match_candidate(results[0], prefetch_genres=False)
        except BaseException as e:
            logger.warning("Exception caught while searching TMDB by IMDB: {}. {}".format(imdbid, e))
            return None
    
    @staticmethod
    def get_by_id(id):
        movie = tmdb.Movies(int(id)).info()
        logger.debug("Fetched TMDB movie by id {}, result: {}".format(id, movie))
        return TMDBApi._tmdb_to_movie_match_candidate(movie, prefetch_genres=False)
