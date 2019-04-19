from sqlalchemy import or_

from banana.media.item import ParsedMediaItem
from banana.media.model import MovieMatchCandidate
from banana.movies.model import Movie


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

    @staticmethod
    def search(title: str = None, job_id: str = None, limit=3) -> dict:

        qbe = ()

        if title:
            qbe += (
                Movie.title.like(f'%{title}%'),
                Movie.original_title.like(f'%{title}%')
            )

        if job_id:
            qbe += (
                ParsedMediaItem.job_id == job_id
            )

        total_results = Movie.query.filter(or_(*qbe)).count()

        movies = Movie.query.join(ParsedMediaItem).filter(or_(*qbe)).limit(limit)

        results = []
        for m in movies:
            results.append({
                "title": m.title,
                "original_title": m.original_title,
                "poster": m.poster,
                "plot": m.plot,
                "release_year": m.release_year,
                "source_id": m.id,
                "source": "local"
            })

        return {'total_results': total_results, 'results': results}
