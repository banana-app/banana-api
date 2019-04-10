import uuid

import rx

from enum import Enum

from banana.media.observables.fixmatch import FixMatchObservable
from banana.media.observables.manualmatchig import ManualMatchingObservable
from banana.media.targets import get_media_target_resolver, MediaTargetResolver
from banana.movies.model import MovieMatchRequest
from .observers import MediaScannerProgressEventObserver, MediaScannerCompletedOrErrorEventObserver, \
    MediaItemMatchingObserver, \
    ManualMediaItemMatchingObserver, ManualMatchProgressEventObserver, ManualMatchCompletedOrErrorEventObserver, \
    FixMatchObserver, FixMatchProgressEventObserver, FixMatchCompletedOrErrorEventObserver
from banana.media.observables.mediascanner import FileSystemMediaScanner
from ..core import JobContext, Runnable, Config


class JobTypes(Enum):

    MEDIA_SCANNER = 'media_scanner'
    MANUAL_MATCH = 'manual_match'
    FIX_MATCH = 'fix_match'


class FileSystemScanJob(JobContext, Runnable):

    def __init__(self):
        self._id: str= str(uuid.uuid4())
        self._type: str = JobTypes.MEDIA_SCANNER.value

    def id(self):
        return self._id

    def type(self):
        return self._type

    def run(self, scheduler):
        scanner = FileSystemMediaScanner(self)
        media_items_to_scan = scanner.media_items_to_scan()
        scanner_observable = rx.Observable.create(scanner).zip(rx.Observable.
                                                    from_iterable(range(media_items_to_scan), scheduler), lambda x, y: (y+1, x))
        subject = rx.subjects.Subject()
        subject.subscribe(MediaItemMatchingObserver(self))
        subject.subscribe(MediaScannerProgressEventObserver(self, total_items=media_items_to_scan))
        subject.subscribe(MediaScannerCompletedOrErrorEventObserver(self))

        scanner_observable.subscribe_on(scheduler).flat_map(lambda x: rx.Observable.just(x, scheduler))\
            .subscribe(subject)


class ManualMovieMatchJob(JobContext, Runnable):

    def __init__(self, match_request: MovieMatchRequest,
                 resolver: MediaTargetResolver = get_media_target_resolver(Config.media_target_resolver())
                 ):
        self._id: str = str(uuid.uuid4())
        self._type: str = JobTypes.MANUAL_MATCH.value
        self._match_request = match_request
        self._resolver = resolver

    def id(self):
        return self._id

    def type(self):
        return self._type

    def run(self, scheduler):
        manual_matcher = rx.Observable.create(ManualMatchingObservable(self, self._match_request))
        subject = rx.subjects.Subject()
        subject.subscribe(ManualMediaItemMatchingObserver(self))
        subject.subscribe(ManualMatchProgressEventObserver(self))
        subject.subscribe(ManualMatchCompletedOrErrorEventObserver(self))
        manual_matcher.subscribe_on(scheduler).subscribe(subject)


class FixMatchJob(JobContext, Runnable):

    def __init__(self,
                 media_id: int,
                 match_request: MovieMatchRequest,
                 resolver: MediaTargetResolver = get_media_target_resolver(Config.media_target_resolver())
                 ):
        self._id: str = str(uuid.uuid4())
        self._media_id = media_id
        self._type: str = JobTypes.MANUAL_MATCH.value
        self._match_request = match_request
        self._resolver = resolver

    def id(self):
        return self._id

    def type(self):
        return self._type

    def run(self, scheduler):
        manual_matcher = rx.Observable.create(FixMatchObservable(self,
                                                                 match_request=self._match_request,
                                                                 media_id=self._media_id))
        subject = rx.subjects.Subject()
        subject.subscribe(FixMatchObserver(self))
        subject.subscribe(FixMatchProgressEventObserver(self))
        subject.subscribe(FixMatchCompletedOrErrorEventObserver(self))
        manual_matcher.subscribe_on(scheduler).subscribe(subject)
