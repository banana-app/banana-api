import uuid
from abc import abstractmethod
from enum import Enum

import rx

from ..media.observables.mediascanner import FileSystemMediaScanner
from .observers import MediaScannerProgressEventObserver, MediaScannerCompletedOrErrorEventObserver, \
    MediaItemMatchingObserver, \
    ManualMediaItemMatchingObserver, ManualMatchProgressEventObserver, ManualMatchCompletedOrErrorEventObserver, \
    FixMatchObserver, FixMatchProgressEventObserver, FixMatchCompletedOrErrorEventObserver, ParsedMediaItem, \
    EmitEventMixin, JobProgressEvent, JobCompletedEvent
from ..core import JobContext, Runnable, Config, socket as web_socket
from ..media.observables.fixmatch import FixMatchObservable
from ..media.observables.manualmatchig import ManualMatchingObservable
from ..media.targets import get_media_target_resolver, MediaTargetResolver
from ..movies.model import MovieMatchCandidate


class JobTypes(Enum):

    MEDIA_SCANNER = 'media_scanner'
    MANUAL_MATCH = 'manual_match'
    FIX_MATCH = 'fix_match'
    GENERIC = 'generic'


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

    def __init__(self,
                 media: ParsedMediaItem,
                 candidate: MovieMatchCandidate):
        self._id: str = str(uuid.uuid4())
        self._type: str = JobTypes.MANUAL_MATCH.value
        self._media = media
        self._candidate = candidate

    def id(self):
        return self._id

    def type(self):
        return self._type

    def run(self, scheduler):
        manual_matcher = rx.Observable.create(ManualMatchingObservable(self, self._media, self._candidate))
        subject = rx.subjects.Subject()
        subject.subscribe(ManualMatchProgressEventObserver(self))
        subject.subscribe(ManualMediaItemMatchingObserver(self))
        subject.subscribe(ManualMatchCompletedOrErrorEventObserver(self))
        manual_matcher.subscribe_on(scheduler).subscribe(subject)


class FixMatchJob(JobContext, Runnable):

    def __init__(self,
                 media: ParsedMediaItem,
                 candidate: MovieMatchCandidate,
                 resolver: MediaTargetResolver = get_media_target_resolver(Config.media_target_resolver())
                 ):
        self._id: str = str(uuid.uuid4())
        self._media = media
        self._type: str = JobTypes.FIX_MATCH.value
        self._candidate = candidate
        self._resolver = resolver

    def id(self):
        return self._id

    def type(self):
        return self._type

    def run(self, scheduler):
        manual_matcher = rx.Observable.create(FixMatchObservable(self,
                                                                 media=self._media,
                                                                 candidate=self._candidate))
        subject = rx.subjects.Subject()
        subject.subscribe(FixMatchProgressEventObserver(self))
        subject.subscribe(FixMatchObserver(self))
        subject.subscribe(FixMatchCompletedOrErrorEventObserver(self))
        manual_matcher.subscribe_on(scheduler).subscribe(subject)


class GenericSyncJob(JobContext, Runnable, EmitEventMixin):

    def __init__(self, socket = web_socket):
        super(GenericSyncJob, self).__init__()
        self._id = str(uuid.uuid4())
        self._type = JobTypes.GENERIC.value
        self._socket = web_socket

    def id(self) -> str:
        return self._id

    def type(self):
        return self._type

    @abstractmethod
    def operation(self):
        raise NotImplementedError('Operation should be patched before call.')

    @classmethod
    def from_callable(cls, op):
        class _GenericSyncJob(cls):

            def operation(self):
                op()

        return _GenericSyncJob()

    def run(self, scheduler):
        self.emit(self._socket, JobProgressEvent(self.id(), self.type()))
        self.operation()
        self.emit(self._socket, JobCompletedEvent(self.id(), self.type()))

