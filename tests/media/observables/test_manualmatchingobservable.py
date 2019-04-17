import unittest
from unittest.mock import MagicMock

import rx

from banana.core import app
from banana.media.item import *
from banana.media.model import *
from banana.media.observables.manualmatchig import ManualMatchingObservable
from banana.media.observers import ManualMediaItemMatchingObserver, JobErrorEvent, JOB_NAMESPACE
from banana.media.sources import LocalSource
from banana.media.targets import SkipExistingMediaTargetResolver, NoOpMediaTargetBuilder
from banana.movies.model import *
from tests.fixtures import MockJobContext, MockWebSocket


class ErrorCatchingObserver(rx.Observer):

    def __init__(self):
        self.error = False

    def on_next(self, value):
        pass

    def on_completed(self):
        pass

    def on_error(self, error):
        self.error = True


class ManualMatchingObservableTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
        self.db = db
        self.db.drop_all()
        self.db.create_all()

    def test_manual_match(self):
        # Given
        context = MockJobContext()
        media = ParsedMediaItem(filename='Monthy Python 1969.mp4', title='Monthy Python', year='1969')
        candidate = MovieMatchCandidate(title='Monthy Python', release_year=1969)
        unmatched = UnmatchedItem(potential_matches=[candidate], parsed_media_item=media,
                                  non_match_reason=NonMatchReason.LOW_TRESHOLD)

        db.session.add(unmatched)
        db.session.commit()
        request = MovieMatchRequest(match_type='local',
                                    match_type_id=candidate.id,
                                    unmatched_item_id=unmatched.id)

        source_factory = MagicMock(return_value=LocalSource)
        matching_observable = ManualMatchingObservable(context, match_request=request, source_factory=source_factory)
        resolver = SkipExistingMediaTargetResolver(media_target_builder=NoOpMediaTargetBuilder())
        matching_observer = ManualMediaItemMatchingObserver(context, resolver=resolver)

        # When

        rx.Observable.create(matching_observable).subscribe(matching_observer)

        # Then

        matched_movie = Movie.query.filter_by(title='Monthy Python').one_or_none()

        self.assertEquals(0, UnmatchedItem.query.count())
        self.assertEquals(1, Movie.query.count())
        self.assertIsNotNone(matched_movie)
        self.assertEquals('Monthy Python', matched_movie.title)

    def test_observable_error(self):
        # Given
        # We have Unmatched Item in db, with media and one candidate
        # and INVALID match request
        context = MockJobContext()
        media = ParsedMediaItem(id=1, filename='Monthy Python 1969.mp4', title='Monthy Python', year='1969')
        candidate = MovieMatchCandidate(id=7, title='Monthy Python', release_year=1969)
        unmatched = UnmatchedItem(id=3, potential_matches=[candidate], parsed_media_item=media,
                                  non_match_reason=NonMatchReason.LOW_TRESHOLD)

        db.session.add(unmatched)
        db.session.commit()

        request = MovieMatchRequest(match_type='THIS SHOULD FAIL',
                                    match_type_id=None,
                                    unmatched_item_id=None)

        source_factory = MagicMock(return_value=LocalSource)
        matching_observable = ManualMatchingObservable(context, match_request=request, source_factory=source_factory)
        resolver = SkipExistingMediaTargetResolver(media_target_builder=NoOpMediaTargetBuilder())
        matching_observer = ManualMediaItemMatchingObserver(context, resolver=resolver)

        # When
        # we submit manual match job

        subject = rx.subjects.Subject()
        error_catching_observer = ErrorCatchingObserver()
        subject.subscribe(matching_observer)
        subject.subscribe(error_catching_observer)

        rx.Observable.create(matching_observable).subscribe(subject)

        # Then
        # it should call ErrorCatchingObserver on_error method
        # and database should stay untouched

        self.assertEqual(1, UnmatchedItem.query.count())
        self.assertEqual(0, Movie.query.count())
        self.assertTrue(error_catching_observer.error)

    def test_observer_error(self):
        # Given
        # We have unmatched item in database, with valid media item and one movie match candidate
        # and VALID MovieMatchRequest
        context = MockJobContext()
        media = ParsedMediaItem(filename='Monthy Python 1969.mp4', title='Monthy Python', year='1969')
        candidate = MovieMatchCandidate(title='Monthy Python', release_year=1969)
        unmatched = UnmatchedItem(potential_matches=[candidate], parsed_media_item=media,
                                  non_match_reason=NonMatchReason.LOW_TRESHOLD)

        db.session.add(unmatched)
        db.session.commit()

        request = MovieMatchRequest(match_type='local',
                                    match_type_id=candidate.id,
                                    unmatched_item_id=unmatched.id)

        source_factory = MagicMock(return_value=LocalSource)
        matching_observable = ManualMatchingObservable(context, match_request=request, source_factory=source_factory)

        # When
        # we have mocked media target resolver, which will raise exception
        # within ManualMediaItemMatchingObserver
        resolver = SkipExistingMediaTargetResolver(media_target_builder=NoOpMediaTargetBuilder())
        resolver.resolve = MagicMock(side_effect=ValueError("Some Exception"))

        socket = MockWebSocket()
        socket.emit = MagicMock()

        matching_observer = ManualMediaItemMatchingObserver(context, resolver=resolver, web_socket=socket)
        rx.Observable.create(matching_observable).subscribe(matching_observer)

        # Then
        # database should stay untouched and
        # Observer should emit JobErrorEvent using web socket
        self.assertEqual(1, UnmatchedItem.query.count())
        self.assertEqual(0, Movie.query.count())
        event = JobErrorEvent(job_id=context.id(), job_type=context.type(), context="Some Exception")
        socket.emit.assert_called_with(context.type(), event.to_json(), namespace=JOB_NAMESPACE)


