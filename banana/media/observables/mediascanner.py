import uuid
import os
import rx
import traceback

from banana.media.item import ParsedMediaItem
from banana.core import JobContext, Runnable, Config, getLogger
from banana.media.p import MediaParser

import filetype


class FileSystemMediaScanner(object):
    """
    A callable here, which is transformed to rx.Observable with Observable.create factory method.

    This class scans a given directory for media to match and feeds Observers with parsed media files. Observers are
    responsible for an actual match.

    It has an unique ID for every running scanner job.
    """

    def __init__(self,
                 job_context: JobContext,
                 media_scan_path: str = Config.media_scan_path(),
                 skip_filetype_checks: bool = Config.media_scanner_skip_filetype_checks()):

        self._job_context = job_context
        self._media_scan_path = media_scan_path
        self._media_source = os.walk(media_scan_path)
        self._total_items = sum([len(files) for _, _, files in os.walk(media_scan_path)])
        self.logger = getLogger(self.__class__.__name__)
        self.skip_filetype_checks = skip_filetype_checks
        self.media_parser = MediaParser()

    def media_items_to_scan(self) -> int:
        return self._total_items

    def __call__(self, observer: rx.Observer):

        def is_supported_filetype(path, file):
            # noinspection PyBroadException
            try:
                f = os.path.join(path, file)
                self.logger.debug(f"Checking if {f} is supported by this scanner...")
                return filetype.video(f) is not None
            except:
                return False

        self.logger.info(f"Starting scan job: {self._job_context.id()} for a folder: {self._media_scan_path}")

        for current_dir_name, subdirectories, files in self._media_source:
            for f in files:

                media = self.media_parser.parse(f)

                # noinspection PyBroadException
                try:
                    if not self.skip_filetype_checks and \
                            not is_supported_filetype(current_dir_name, f):
                        self.logger.info(f'File {f} is not supported by this scanner. Skipping.')
                    else:
                        self.logger.debug(f"Processing {f}...")
                        media = ParsedMediaItem(filename=f,
                                                path=current_dir_name,
                                                audio=media.get("audio"),
                                                codec=media.get("codec"),
                                                container=media.get("container"),
                                                episode=media.get("episode"),
                                                episodeName=media.get("episodeName"),
                                                garbage=media.get("garbage"),
                                                group=media.get("group"),
                                                hardcoded=media.get("hardcoded"),
                                                language=media.get("language"),
                                                proper=media.get("proper"),
                                                quality=media.get("quality"),
                                                region=media.get("region"),
                                                repack=media.get("repack"),
                                                resolution=media.get("resolution"),
                                                season=media.get("season"),
                                                title=media.get("title"),
                                                website=media.get("website"),
                                                widescreen=media.get("widescreen"),
                                                year=media.get("year"))

                        observer.on_next(media)

                except BaseException as e:
                    self.logger("FileSystemMediaScanner caught exception", traceback.format_exc())
                    observer.on_error(e)

        self.logger.info(f"Completed file scan job: {self._job_context.id()} for a folder {self._media_scan_path}")
        observer.on_completed()


class MediaScanJob(JobContext, Runnable):

    def __init__(self, path_to_scan: str):
        self._id = str(uuid.uuid4())
        self._type = JobContext.SCAN_JOB
        self.logger = getLogger(self.__class__.__name__)

    def id(self):
        return self._id

    def type(self):
        return self._type

    def run(self, scheduler):
        pass
