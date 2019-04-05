from banana.core import db
from banana.media.model import MovieMatchCandidate


class LocalSource(object):
    """
    This is just for consistency. This basic source can lookup match candidates we have already
    in banana.
    """

    @staticmethod
    def get_by_id(match_id: str) -> MovieMatchCandidate:
        """
        Returns Movie match candidate from the local database, or none if does not exist.

        :param match_id: local MovieMatchCandidate id
        :return: MovieMatchCandidate
        """
        return MovieMatchCandidate.query.filter_by(id=int(match_id)).one_or_none()
