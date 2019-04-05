import unittest
import funcy
from whatever import _

from banana.movies.model import MovieMatchCandidate
from banana.movies.matchdecider import MatchDecider, MatchType, NonMatchReason

class MatchDeciderTest(unittest.TestCase):

    def test_low_threshold(self):
        match_candidates = [MovieMatchCandidate(match=45),
                            MovieMatchCandidate(match=28),
                            MovieMatchCandidate(match=10)]

        decider = MatchDecider()
        match = decider.try_match(match_candidates)

        self.assertIsNotNone(match)
        self.assertEqual(MatchType.UNMATCHED, match.match_type())
        self.assertEqual(NonMatchReason.LOW_TRESHOLD, match.reason())
        self.assertEqual(3, len(match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 45, match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 28, match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 10, match.potential_matches()))

    def test_multiple_candidates_with_same_ratio(self):
        match_candidates = [MovieMatchCandidate(match=92),
                            MovieMatchCandidate(match=92),
                            MovieMatchCandidate(match=81),
                            MovieMatchCandidate(match=80)]

        decider = MatchDecider()
        match = decider.try_match(match_candidates)

        self.assertIsNotNone(match)
        self.assertEqual(MatchType.UNMATCHED, match.match_type())
        self.assertEqual(NonMatchReason.MULTIPLE_CANDIDATES, match.reason())
        self.assertEqual(4, len(match.potential_matches()))
        self.assertTrue(funcy.any(_.match == 92, match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 81, match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 80, match.potential_matches()))

    def test_perfect_match(self):
        match_candidates = [MovieMatchCandidate(match=92),
                            MovieMatchCandidate(match=90),
                            MovieMatchCandidate(match=81)]

        decider = MatchDecider()
        match = decider.try_match(match_candidates)

        self.assertIsNotNone(match)
        self.assertEqual(MatchType.MATCHED, match.match_type())
        self.assertEqual(match_candidates[0].to_movie(), match.matched_movie())
        self.assertEqual(2, len(match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 92, match.potential_matches()))
        self.assertTrue(funcy.one(_.match == 90, match.potential_matches()))

