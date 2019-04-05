from .imdb import IMDBApi
from .tmdb import TMDBApi
from .local import LocalSource

_source_mappings = {
    "imdb": IMDBApi,
    "tmdb": TMDBApi,
    "local": LocalSource
}


def get_media_source(source: str):
    """
    Media source factory method.
    :param source: A string id for a source (imdb, tmdb, local)
    :return: API for a given source
    """
    return _source_mappings.get(source)
