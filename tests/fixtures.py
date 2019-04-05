import uuid

from banana.core.jobs import JobContext


class MockJobContext(JobContext):

    def __init__(self, id: str = uuid.uuid4()):
        self._id = str(id)

    def id(self):
        return self._id

    def type(self):
        return 'mock job context'


class MockWebSocket:

    def emit(self):
        pass
