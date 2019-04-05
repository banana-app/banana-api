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
    Unfortunately we cannot easily create and rx Observable class, yet we would like to keep some state with it.
    Using simple functional generator here is very inconvenient. So we basically are creating a callable here, which
    then should be translated into rx.Observable with Observable.create factory method.

    This class basically scans a given directory and feeds Observers with parsed media files.

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

    def __iter__(self):

        def is_supported_filetype(path, file):
            try:
                f = os.path.join(path, file)
                self.logger.debug("Checking if {} is supported by this scanner...".format(f))
                return filetype.video(f) is not None
            except:
                return False

        self.logger.info("Starting scan job: {} for a folder: {}".format(self._job_context.id(), self._media_scan_path))

        for current_dir_name, subdirectories, files in self._media_source:
            for f in files:

                media = self.media_parser.parse(f)

                try:
                    if not self.skip_filetype_checks and \
                            not is_supported_filetype(current_dir_name, f):
                        self.logger.info('File {} is not supported by this scanner. Skipping.'.format(f))
                    else:
                        self.logger.debug("Processing {}...".format(f))
                        parsed_media_item = ParsedMediaItem(filename=f,
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

                        yield parsed_media_item

                except BaseException as e:
                    self.logger("FileSystemMediaScanner caught exception", traceback.format_exc())


        self.logger.info("Completed file scan job: {} for a folder {}".format(self._job_context.id(),
                                                                              self._media_scan_path))
        #raise StopIteration


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
