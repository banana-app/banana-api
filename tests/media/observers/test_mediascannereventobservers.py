import unittest
import pathlib
import tempfile

from unittest.mock import MagicMock
from banana.media.observers.eventobservers import *
from banana.media.observables.mediascanner import FileSystemMediaScanner

from tests.fixtures import MockJobContext, MockWebSocket


class MediaScannerEventObserversTest(unittest.TestCase):

    _files = ['A Foo Bar 1999 1080p BluRay.mkv', 'B Quux 720p.mkv']

    def setUp(self):
        self.job_context = MockJobContext()
        self.temp_dir = tempfile.mkdtemp()
        pathlib.Path(self.temp_dir, self._files[0]).touch()
        pathlib.Path(self.temp_dir, self._files[1]).touch()

    def test_emit_progress_events(self):
        scanner = FileSystemMediaScanner(media_scan_path=self.temp_dir,
                                         job_context=self.job_context, skip_filetype_checks=True)
        scanner_observer = rx.Observable.create(scanner)

        sock = MockWebSocket()
        sock.emit = MagicMock()
        event = JobProgressEvent(job_id=self.job_context.id(),
                                 job_type=self.job_context.type(),
                                 current_item=2,
                                 context=self._files[0]).to_json()

        scanner_observer.zip(rx.Observable.from_iterable(range(1, len(self._files))), lambda x, y: (y+1, x))\
            .subscribe(MediaScannerProgressEventObserver(self.job_context, sock))
        sock.emit.assert_called_with(self.job_context.type(), event, namespace=JOB_NAMESPACE)

    def test_emit_finished_events(self):
        scanner = FileSystemMediaScanner(media_scan_path=self.temp_dir,
                                         job_context=self.job_context, skip_filetype_checks=True)
        scanner_observer = rx.Observable.create(scanner)

        sock = MockWebSocket()
        sock.emit = MagicMock()

        event = JobCompletedEvent(job_id=self.job_context.id(), job_type=self.job_context.type()).to_json()

        scanner_observer.subscribe(MediaScannerCompletedOrErrorEventObserver(self.job_context, sock))
        sock.emit.assert_called_once_with(self.job_context.type(), event, namespace=JOB_NAMESPACE)

    def test_emit_error_event(self):

        def mock_media_scanner(observer: rx.Observer):
            observer.on_error(error='some error')

        scanner_observer = rx.Observable.create(mock_media_scanner)

        sock = MockWebSocket()
        sock.emit = MagicMock()

        event = JobErrorEvent(job_id=self.job_context.id(), job_type=self.job_context.type(), cause="some error").to_json()

        scanner_observer.subscribe(MediaScannerCompletedOrErrorEventObserver(self.job_context, sock))
        sock.emit.assert_called_once_with(self.job_context.type(), event, namespace=JOB_NAMESPACE)








