from abc import ABC, abstractmethod
from enum import Enum
from typing import List

from ..core import app
import banana.movies.model as movies

from funcy import select, one
from whatever import _


class MovieMatchException(Exception):
    def __init__(self, message):
        self.message = message


class MatchType(Enum):
    MATCHED = 1
    UNMATCHED = 2


class NonMatchReason(Enum):
    MULTIPLE_CANDIDATES = 1
    LOW_TRESHOLD = 2


# Match ABC interface
class Match(ABC):
    """
    An abstract class representing Matching result by MatchDecider.
    """

    @abstractmethod
    def match_type(self) -> MatchType:
        """
        It's a match type for this match result.
        :return: match type
        """
        pass

    @abstractmethod
    def potential_matches(self) -> List[movies.MovieMatchCandidate]:
        """
        Potential match candidates for this movie.
        :return: ma tch candidates
        """
        pass


class PerfectMatch(Match):
    """
    PerfectMatch is class keeping perfectly matched Movie by MatchDecider.

    :param matched_movie - is a movie instance matched by MatchDecider
    :param potential_matches - a list of MovieMatchCandidates used to match against this movie

    """
    def __init__(self, matched_movie: movies.Movie, potential_matches: List[movies.MovieMatchCandidate]):
        self._potential_matches: List[movies.MovieMatchCandidate] = potential_matches
        self._matched_movie: movies.Movie = matched_movie

    def match_type(self) -> MatchType:
        return MatchType.MATCHED

    def potential_matches(self) -> List[movies.MovieMatchCandidate]:
        return self._potential_matches

    def matched_movie(self) -> movies.Movie:
        return self._matched_movie


class Unmatched(Match):
    """
    Class representing unmatched item, together with the reason for this media file being not matched.

    Media file may be non matched generally because of three reasons:

    * All potential matches are under acceptable threshold
    * There are multiple movies, above the threshold, but with the same match ratio
    * There was an general error matching the movie

    This class captures this.
    """

    def __init__(self, potential_matches: List[movies.MovieMatchCandidate], reason: NonMatchReason):
        self._reason: NonMatchReason = reason
        self._potential_matches: List[movies.MovieMatchCandidate] = potential_matches

    def reason(self) -> NonMatchReason:
        return self._reason

    def match_type(self) -> MatchType:
        return MatchType.UNMATCHED

    def potential_matches(self) -> List[movies.MovieMatchCandidate]:
        return self._potential_matches


class MatchDecider(object):

    def try_match(self,
                  candidates: List[movies.MovieMatchCandidate],
                  threshold=int(app.config.get('BANANA_MATCHER_THRESHOLD', 90))
                  ) -> Match:

        acceptable_candidates = select(_.match >= threshold, candidates)
        number_of_acceptable_candidates = len(acceptable_candidates)

        def can_match():
            if number_of_acceptable_candidates > 0:
                return one(_.match == acceptable_candidates[0].match, acceptable_candidates)
            return False

        if can_match():
            movie = acceptable_candidates[0].to_movie()
            return PerfectMatch(matched_movie=movie, potential_matches=acceptable_candidates)
        else:
            if number_of_acceptable_candidates == 0:
                return Unmatched(candidates, NonMatchReason.LOW_TRESHOLD)
            else:
                return Unmatched(candidates, NonMatchReason.MULTIPLE_CANDIDATES)
