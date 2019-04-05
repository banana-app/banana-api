from fuzzywuzzy import fuzz
from typing import List
from abc import ABC, abstractmethod

from ..movies.model import MovieMatchCandidate
from ..media.item import ParsedMediaItem
from ..common.common import canonical_movie_title
from ..core import app, getLogger

from banana.media.sources import get_media_source

logger = getLogger(__name__)


class Matcher(ABC):

    @abstractmethod
    def top5_matches(self, parsed_media_item: ParsedMediaItem) -> List[MovieMatchCandidate]:
        pass


class SourceMatcher(Matcher):

    def __init__(self, source):
        self.source = source

    def top5_matches(self, parsed_media_item):
        """
        This is basic matcher, used to match against TMDB first (which is fast), and when we dont have any match
        candidates from this source as a fallback strategy we trying to match against (slow) IMDB.

        This approach, while fast and effective has some drawbacks: We may have TMDB results below match threshold
        (probably something that should not be matched), while we may have found better match candidates on IMDB.
        We could have do matching for both sources in parallel and then select best results from both of them,
        but again, we would need to deduplicate things, as we would have same movies matched from different sources.
        We could potentially use TMDB capability to find movie by IMDB id and try to dedup entries against it. This
        would be slow, but probably effective.

        This probably will be pluggable 'match strategy' in future.

        :param parsed_media_item: and media item to match
        :return: list of movie match candidates for a given media item
        """
        return _top5_matches(parsed_media_item, self.source)


class FallbackSourceMatcher(Matcher):

    def __init__(self, primary, secondary):
        self.primary_source = primary
        self.secondary_source = secondary

    def top5_matches(self, parsed_media_item):
        """
        This is basic matcher, used to match against TMDB first (which is fast), and when we dont have any match
        candidates from this source as a fallback strategy we trying to match against (slow) IMDB.

        :param parsed_media_item: and media item to match
        :return: list of movie match candidates for a given media item
        """
        tmdb_results = _top5_matches(parsed_media_item, match_source=self.primary_source)
        if len(tmdb_results) == 0:
            return _top5_matches(parsed_media_item, match_source=self.secondary_source)
        else:
            return tmdb_results


class CompositeSourceMatcher(Matcher, ABC):

    def __init__(self, primary, secondary):
        self.primary_source = primary
        self.secondary_source = secondary

    def _find_candidate_by_tmdbid(self, tmdb_id, matches: List[MovieMatchCandidate]):
        return next(filter(lambda m: m.external_id == tmdb_id, matches), None)

    def _dedup_matches(self, tmdb_matches, imdb_matches) -> List[MovieMatchCandidate]:

        unique_matches = []

        for im in imdb_matches:
            tmdb_movie = self.primary_source.get_by_imdbid_id(im.external_id)
            if not tmdb_movie:
                # We did not find this movie in TMBD source; assume this is not dupe. Add to the list.
                unique_matches.append(im)
                continue
            else:
                # We have this movie in TMDB source; now check if we have this within the list of existing candidates
                matched_tmdb_movie = self._find_candidate_by_tmdbid(tmdb_movie.external_id, tmdb_matches)
                if not matched_tmdb_movie:
                    # if not, assume this is the new movie and just add this to the list
                    unique_matches.append(im)
                else:
                    # If yes, ie. we have this movie on the list, but IMDB match may have better match ratio (say
                    # IMDB source has more complete data and we can match it better
                    if matched_tmdb_movie.match < im.match:
                        # if IMDB.mat > TMDB.match keep only IMDB, remove TMDB from the matches
                        unique_matches.append(im)
                        tmdb_matches.remove(matched_tmdb_movie)
                    else:
                        # We have this already and it's matched with better ratio; skipping it
                        continue

        return sorted(unique_matches + tmdb_matches, key=lambda m: m.match, reverse=True)[:5]


class ParallelMatcher(CompositeSourceMatcher):

    def __init__(self, primary, secondary):
        super().__init__(primary, secondary)

    def top5_matches(self, parsed_media_item):
        """
        This is basic matcher, used to match against TMDB first (which is fast), and when we dont have any match
        candidates from this source as a fallback strategy we trying to match against (slow) IMDB.

        :param parsed_media_item: and media item to match
        :return: list of movie match candidates for a given media item
        """
        tmdb_results = _top5_matches(parsed_media_item, match_source=self.primary_source)
        imdb_results = _top5_matches(parsed_media_item, match_source=self.secondary_source)

        return self._dedup_matches(tmdb_matches=tmdb_results, imdb_matches=imdb_results)


class FallbackLowThresholdSourceMatcher(CompositeSourceMatcher):

    def __init__(self, primary, secondary):
        super().__init__(primary, secondary)

    def top5_matches(self, parsed_media_item):
        """
        This is basic matcher, used to match against TMDB first (which is fast), and when we dont have any match
        candidates from this source as a fallback strategy we trying to match against (slow) IMDB.

        :param parsed_media_item: and media item to match
        :return: list of movie match candidates for a given media item
        """

        tmdb_results = _top5_matches(parsed_media_item, match_source=self.primary_source)
        matched = tmdb_results

        if len(tmdb_results) == 0 or tmdb_results[0].match < int(app.config.get('BANANA_MATCHER_THRESHOLD', 90)):
            imdb_results = _top5_matches(parsed_media_item, match_source=self.secondary_source)
            matched = self._dedup_matches(tmdb_matches=tmdb_results, imdb_matches=imdb_results)

        return matched


_matcher_mapping = {
    'imdb': SourceMatcher(get_media_source('imdb')),
    'tmdb': SourceMatcher(get_media_source('tmdb')),
    'parallel': ParallelMatcher(primary=get_media_source('tmdb'), secondary=get_media_source('imdb')),
    'fallback': FallbackSourceMatcher(primary=get_media_source('tmdb'), secondary=get_media_source('imdb')),
    'low_threshold_fallback': FallbackLowThresholdSourceMatcher(
        primary=get_media_source('tmdb'), secondary=get_media_source('imdb'))
}


def get_matcher(name: str) -> Matcher:
    return _matcher_mapping.get(name)


def _boost_match_ratio_for_closest_release_year(matches: List[MovieMatchCandidate], candidate_year):
    """
    So the idea here is to boos ratio for a movies which are within one year of release date.
    Often movie files hae +/-1 year difference in the names.

    :param matches: a list of the movies
    :param candidate_year: a candidate to check against
    :return: list movies wit adjusted ratio if applicable
    """
    # lets find if we have multiple candidates with same match ratio

    if not candidate_year or not matches or len(matches) < 2:
        return matches

    top_matches_with_same_ratio = [m for m in matches if m.match == matches[0].match]

    for m in top_matches_with_same_ratio:
        if not m.release_year or m.release_year == candidate_year:
            continue
        else:
            ratio_boost = abs(m.release_year - candidate_year) > 1
            m.match = m.match - 1 if ratio_boost else m.match

    return matches


def _top5_matches(parsed_media_item, match_source):
    """
    Matches media item against match source (IMDB, TMDB for movies).

    It basically searches the source for a given title then tries to calculate a match ratio based on
    similarity between canonical titles from media item and source (IMDB, TMDB) results. A canonical title is
    just title and year: 'Monty Python and the Holy Grail (1975)'. This gives pretty good results
    for decent movie identification.

    It checks original title or alternative titles (if available) for a given source as well.

    The it sorts results from best match till the worst one, and returns top 5 entries.

    :param parsed_media_item: media item to match
    :param match_source: a source to match against (IMDB, TMDB)
    :return: an array of MovieMatchCandidates
    """
    logger.info("Matching {}".format(parsed_media_item))

    match_candidates = match_source.match(title=parsed_media_item.title)

    canonical_title = canonical_movie_title(parsed_media_item.title, parsed_media_item.year).lower()

    logger.info(match_candidates)

    results = []
    for m in match_candidates:

        match_ratio = fuzz.ratio(canonical_title.lower(), m.canonical_title().lower())
        candidate_year = m.release_year
        logger.debug("Matched {} against {} with ratio: {}".format(canonical_title, m, match_ratio))

        # if match ratio is not perfect still try to match against original title, if present
        # and if it's different from regular title
        if match_ratio < 100 and m.original_title and not m.original_title == m.title:
            canonical_original_title = canonical_movie_title(m.original_title, candidate_year).lower()
            original_title_match = fuzz.ratio(canonical_title, canonical_original_title)
            if original_title_match > match_ratio:
                match_ratio = original_title_match

        # Check match against akas if we did not find perfect match yet; this is especially important
        # for foreign movies
        if match_ratio < 100 and m.akas:
            akas = m.akas
            logger.debug("Querying for AKAs for {}, got {}".format(canonical_title, akas))
            for aka in akas:
                canonical_aka = canonical_movie_title(aka, candidate_year).lower()
                original_title_match = fuzz.ratio(canonical_title, canonical_aka)
                if original_title_match > match_ratio:
                    match_ratio = original_title_match

        # set calculated match ratio for this match candidate
        m.match = match_ratio
        results.append(m)

    if len(results) < 1:
        logger.info("No matching movies found for {}".format(canonical_title))
        return results

    # Sort all entries by match from best match to the worst and get top 5
    top5_movies_before_boost = sorted(results, key=lambda m: m.match, reverse=True)[:5]

    top5_movies_with_boost = _boost_match_ratio_for_closest_release_year(top5_movies_before_boost,
                                                                         parsed_media_item.year)

    top5_movies = sorted(top5_movies_with_boost, key=lambda m: m.match, reverse=True)[:5]

    logger.debug("Top 5 matches for {} : {}".format(canonical_title, top5_movies))

    return top5_movies
