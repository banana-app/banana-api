import requests
import json


_imdb_suggestions_url = "https://sg.media-imdb.com/suggests/"


def _has_attr(attr, d):
        return attr in d


def _unwrap_jsonp(suggestions: str) -> [dict]:
    """
    Unwraps IMDB suggestions result from jsonp callback. Basically we ignore jsonp; what is interesting is
    suggestions json.

    IMDB sample response:

    imdb$QueryString({ /useful content/... })

    where QueryString is Our term we looking for (title). We just unwrap useful info from jsonp.

    :param suggestions:
    :return: dict with suggestion entries
    """
    return json.loads(suggestions.split("(", 1)[1].strip(")"))


def _filter_movies(suggestions: [dict]) -> [dict]:
    """
    Filter only movies in IMDB suggestions.

    :param suggestions:
    :return: filtered suggestions with only movies
    """
    return list(
        filter(lambda s: _has_attr('q', s) and ('feature' == s.get('q') or 'TV movie' == s.get('q')), suggestions['d'])
    )


def suggest_movie(title: str):
    """
    This is dead simple wrapper for and IMDB suggestions API:
    https://stackoverflow.com/questions/1966503/does-imdb-provide-an-api#7744369

    This is simple, yet quite useful. What is most important it's light-fast compared to PyIMDB API.
    We use this API for quick search capabilities for banana. Anything else requires slower, but more feature rich
    PyIMDB lib.

    :param title: a movie title, or a phrase to get suggestions for
    :return: and list of dictionary with *movie* a suggestions. Anything else would be filtered out.
    """
    return _filter_movies(
        _unwrap_jsonp(
            requests.get(_imdb_suggestions_url + "/" + title[:1].lower() + "/" + title + ".json").text
        )
    )
