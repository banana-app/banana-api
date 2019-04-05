import unittest

from tests import MockJobContext, MockWebSocket


from unittest.mock import MagicMock
import rx

from banana.core import db, app
from banana.media.observables import ManualMatchingObservable
from banana.media.observers import ManualMediaItemMatchingObserver, JobErrorEvent, JOB_NAMESPACE, \
    ManualMatchProgressEventObserver, JobProgressEvent, ManualMatchCompletedOrErrorEventObserver, JobCompletedEvent
from banana.media.sources import LocalSource
from banana.media.targets import SkipExistingMediaTargetResolver, NoOpMediaTargetBuilder
from banana.movies.model import *
from banana.media.model import *
from banana.media.item import *


class ManualMatchingEventObservers(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
        self.db = db
        self.db.drop_all()
        self.db.create_all()

    def test_progress_event(self):
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
        resolver = SkipExistingMediaTargetResolver(media_target_builder=NoOpMediaTargetBuilder())

        socket = MockWebSocket()
        socket.emit = MagicMock()

        matching_observer = ManualMediaItemMatchingObserver(context, resolver=resolver, web_socket=socket)

        subject = rx.subjects.Subject()
        subject.subscribe(ManualMatchProgressEventObserver(job_context=context, socket=socket))
        subject.subscribe(matching_observer)


        rx.Observable.create(matching_observable).subscribe(subject)

        # Then
        # Movie should be matched, we should not have unmatched item and
        # Observer should emit JobProgressEvent using web socket
        self.assertEqual(0, UnmatchedItem.query.count())
        self.assertEqual(1, Movie.query.count())
        event = JobProgressEvent(job_id=context.id(), job_type=context.type())
        socket.emit.assert_called_with(context.type(), event.to_json(), namespace=JOB_NAMESPACE)


    def test_completed_event(self):
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
        resolver = SkipExistingMediaTargetResolver(media_target_builder=NoOpMediaTargetBuilder())

        socket = MockWebSocket()
        socket.emit = MagicMock()

        matching_observer = ManualMediaItemMatchingObserver(context, resolver=resolver, web_socket=socket)

        subject = rx.subjects.Subject()
        subject.subscribe(ManualMatchCompletedOrErrorEventObserver(job_context=context, socket=socket))
        subject.subscribe(matching_observer)

        rx.Observable.create(matching_observable).subscribe(subject)

        # Then
        # Movie should be matched, we should not have unmatched item and
        # Observer should emit JobProgressEvent using web socket
        self.assertEqual(0, UnmatchedItem.query.count())
        self.assertEqual(1, Movie.query.count())
        event = JobCompletedEvent(job_id=context.id(), job_type=context.type())
        socket.emit.assert_called_with(context.type(), event.to_json(), namespace=JOB_NAMESPACE)

    def test_error_event(self):
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

        request = MovieMatchRequest(match_type='SHOLD FAIL',
                                    match_type_id=None,
                                    unmatched_item_id=None)

        source_factory = MagicMock(return_value=LocalSource)
        matching_observable = ManualMatchingObservable(context, match_request=request, source_factory=source_factory)

        # When
        resolver = SkipExistingMediaTargetResolver(media_target_builder=NoOpMediaTargetBuilder())

        socket = MockWebSocket()
        socket.emit = MagicMock()

        matching_observer = ManualMediaItemMatchingObserver(context, resolver=resolver, web_socket=socket)

        subject = rx.subjects.Subject()
        subject.subscribe(ManualMatchCompletedOrErrorEventObserver(job_context=context, socket=socket))
        subject.subscribe(matching_observer)

        rx.Observable.create(matching_observable).subscribe(subject)

        # Then
        # Movie should be matched, we should not have unmatched item and
        # Observer should emit JobProgressEvent using web socket
        self.assertEqual(1, UnmatchedItem.query.count())
        self.assertEqual(0, Movie.query.count())
        event = JobErrorEvent(job_id=context.id(), job_type=context.type())
        socket.emit.assert_called_with(context.type(), event.to_json(), namespace=JOB_NAMESPACE)
