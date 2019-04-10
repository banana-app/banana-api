from typing import Tuple

import rx

from banana.core import socket as web_socket, getLogger
from banana.core.jobs import JobContext
from banana.events import JobProgressEvent, JobCompletedEvent, JobErrorEvent
from banana.media.item import ParsedMediaItem

JOB_NAMESPACE = '/jobs'


class EmitEventMixin(object):

    def __init__(self):
        self.logger = getLogger(__class__.__name__)

    def emit(self, web_socket, event):
        web_socket.emit(event.job_type, event.to_json(), namespace=JOB_NAMESPACE)
        self.logger.debug("Emitting {} with message type '{}' and namespace {}; {}"
                          .format(event.__class__.__name__, event.job_type, JOB_NAMESPACE, event.to_json()))


# noinspection PyBroadException
class MediaScannerCompletedOrErrorEventObserver(EmitEventMixin, rx.Observer):

    def __init__(self, job_context: JobContext, socket=web_socket):
        super().__init__()
        self._job_context = job_context
        self._socket = socket
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, value):
        pass

    def on_completed(self):
        try:
            self.emit(self._socket,
                      JobCompletedEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )

        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobCompletedEvent: {}".format(e))

    def on_error(self, error):
        try:
            self.emit(self._socket,
                      JobErrorEvent(job_id=self._job_context.id(),
                                    job_type=self._job_context.type(),
                                    cause=error)
                      )
        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobErrorEvent: {}".format(e))


# noinspection PyBroadException
class MediaScannerProgressEventObserver(EmitEventMixin, rx.Observer):

    def __init__(self, job_context: JobContext, socket=web_socket, total_items=None):
        super().__init__()
        self._job_context = job_context
        self._socket = socket
        self._total_items = total_items
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, index_and_media: Tuple[int, ParsedMediaItem]):
        try:
            index, media = index_and_media
            self.emit(self._socket,
                      JobProgressEvent(job_id=self._job_context.id(),
                                       job_type=self._job_context.type(),
                                       context=media.filename,
                                       total_items=self._total_items,
                                       current_item=index)
                      )
        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobProgressEvent: {}".format(e))

    def on_error(self, error):
        pass

    def on_completed(self):
        pass


class ManualMatchCompletedOrErrorEventObserver(EmitEventMixin, rx.Observer):

    def __init__(self, job_context: JobContext, socket=web_socket):
        super().__init__()
        self._job_context = job_context
        self._socket = socket
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, value):
        pass

    def on_completed(self):
        try:
            self.emit(self._socket,
                      JobCompletedEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )

        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobCompletedEvent: {}".format(e))

    def on_error(self, error):
        try:
            self.emit(self._socket,
                      JobErrorEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )
        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobErrorEvent: {}".format(e))


# noinspection PyBroadException
class ManualMatchProgressEventObserver(EmitEventMixin, rx.Observer):

    def __init__(self, job_context: JobContext, socket=web_socket):
        super().__init__()
        self._job_context = job_context
        self._socket = socket
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, value):
        try:
            self.emit(self._socket,
                      JobProgressEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )
        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobProgressEvent: {}".format(e))

    def on_error(self, error):
        pass

    def on_completed(self):
        pass


class FixMatchCompletedOrErrorEventObserver(EmitEventMixin, rx.Observer):

    def __init__(self, job_context: JobContext, socket=web_socket):
        super().__init__()
        self._job_context = job_context
        self._socket = socket
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, value):
        pass

    def on_completed(self):
        try:
            self.emit(self._socket,
                      JobCompletedEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )

        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobCompletedEvent: {}".format(e))

    def on_error(self, error):
        try:
            self.emit(self._socket,
                      JobErrorEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )
        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobErrorEvent: {}".format(e))


# noinspection PyBroadException
class FixMatchProgressEventObserver(EmitEventMixin, rx.Observer):

    def __init__(self, job_context: JobContext, socket=web_socket):
        super().__init__()
        self._job_context = job_context
        self._socket = socket
        self.logger = getLogger(self.__class__.__name__)

    def on_next(self, value):
        try:
            self.emit(self._socket,
                      JobProgressEvent(job_id=self._job_context.id(), job_type=self._job_context.type())
                      )
        except BaseException as e:
            self.logger.warning("Exception caught while emitting JobProgressEvent: {}".format(e))

    def on_error(self, error):
        pass

    def on_completed(self):
        pass
