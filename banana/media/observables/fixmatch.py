import rx

from banana.core import JobContext, getLogger
from banana.media.item import ParsedMediaItem
from banana.movies.model import MovieMatchCandidate


class FixMatchObservable:
    """
    This observable handles fix match request from UI (meaning that user manually chooses a movie candidate to fix match
    of a ParsedMediaItem). MovieMatchRequest input carries all required information:

    See [ManualMatchingObservable] for all details.
    """

    def __init__(self,
                 job_context: JobContext,
                 media: ParsedMediaItem,
                 candidate: MovieMatchCandidate):
        super().__init__()
        self._media = media
        self._job_context = job_context
        self.logger = getLogger(self.__class__.__name__)
        self._candidate = candidate

    def __call__(self, observer: rx.Observer):
        """
        It emits an event to the observers with ParsedMediaItem and movie match candidate to fix match for that item.
        :param observer - an Observer to fix match.
        """
        try:
                observer.on_next((self._media, self._candidate))
                observer.on_completed()

        except BaseException as e:
            observer.on_error(e)
