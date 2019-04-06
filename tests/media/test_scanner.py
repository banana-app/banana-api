import pathlib
import tempfile
import unittest
import os
import filetype

import rx
from rx.concurrency import ThreadPoolScheduler
from funcy import one
from whatever import _
import time

from banana.media.observables.mediascanner import FileSystemMediaScanner
from tests.fixtures import MockJobContext


class ScannerTest(unittest.TestCase):

    _files = ['A Foo Bar 1999 1080p BluRay.mkv', 'B Quux 720p.mkv']

    _fake_mkv_magic_bytes = [
        0x1A, 0x45,
        0xDF, 0xA3,
        0x93, 0x42,
        0x82, 0x88,
        0x6D, 0x61,
        0x74, 0x72,
        0x6F, 0x73,
        0x6B, 0x61]

    def setUp(self):
        self.job_context = MockJobContext()
        self.temp_dir = tempfile.mkdtemp()
        pathlib.Path(self.temp_dir, self._files[0]).touch()
        pathlib.Path(self.temp_dir, self._files[1]).touch()

    def test_simple_scan(self):
        scanner = FileSystemMediaScanner(media_scan_path=self.temp_dir,
                                         job_context=self.job_context, skip_filetype_checks=True)
        scanner_observer = rx.Observable.create(scanner)

        processed_items = []
        scanner_observer.subscribe(
            on_next=lambda item: processed_items.append(item)
        )

        self.assertEqual(2, len(processed_items))
        self.assertTrue(one(_.filename == 'A Foo Bar 1999 1080p BluRay.mkv', processed_items))
        self.assertTrue(one(_.filename == 'B Quux 720p.mkv', processed_items))

    def test_filetype_scheck(self):
        # Given
        # We have MediaScanner WITH enabled file type check
        # and dummy (non video) files
        scanner = FileSystemMediaScanner(media_scan_path=self.temp_dir, job_context=self.job_context,
                                         skip_filetype_checks=False)
        scanner_observer = rx.Observable.create(scanner)

        # When
        # we start a scan job by subscribing to the scanner
        processed_items = []
        scanner_observer.subscribe(
            on_next=lambda item: processed_items.append(item)
        )

        # Then
        # it should skip all dummy media items
        self.assertEqual(0, len(processed_items))

    def test_fake_mkv(self):
        with open(os.path.join(self.temp_dir, self._files[1]), 'wb') as qoox:
            qoox.write(bytearray(self._fake_mkv_magic_bytes))

        self.assertIsNotNone(filetype.video(os.path.join(self.temp_dir, self._files[1])))


    def test_threadpool_executor(self):

        with open(os.path.join(self.temp_dir, self._files[1]), 'wb') as qoox:
            qoox.write(bytearray(self._fake_mkv_magic_bytes))

        scanner = FileSystemMediaScanner(media_scan_path=self.temp_dir,
                                         job_context=self.job_context, skip_filetype_checks=False)
        scanner_observer = rx.Observable.create(scanner)

        processed_items = []

        subject = rx.subjects.Subject()
        subject.subscribe(on_next=lambda item: '')
        subject.subscribe(on_next=lambda item: '')
        subject.subscribe(on_next=lambda item: processed_items.append(item))

        scanner_observer.subscribe_on(ThreadPoolScheduler(3)).observe_on(ThreadPoolScheduler(3)).subscribe(
            subject
        )
        time.sleep(5)

        self.assertEqual(1, len(processed_items))
        self.assertTrue(one(_.filename == 'B Quux 720p.mkv', processed_items))
