import rx

from banana.core import JobContext, getLogger
from banana.media.item import ParsedMediaItem
from banana.movies.model import MovieMatchCandidate


class ManualMatchingObservable:
    """
    This observable handles manual match request from UI (meaning that user manually chooses a movie candidate to match
    with unmatched media. MovieMatchRequest input carries all required information:

    * a MatchSource (either user decides to match media against tmdb, imdb or already existing (local) movie match
     candidate.
    * a source specific ID: tmdb id if source is 'tmdb', imdb id is source is 'imdb' or UnmatchedItem id is source is
    'local'
    """

    def __init__(self,
                 job_context: JobContext,
                 media: ParsedMediaItem,
                 candidate: MovieMatchCandidate):
        super().__init__()
        self._job_context = job_context
        self.logger = getLogger(self.__class__.__name__)
        self._media = media
        self._candidate = candidate

    def __call__(self, observer: rx.Observer):
        """
        It emits an event to the observers with UnmatchedItem and movie match candidate to match with that item.
        :param observer - an Observer to handle actual match.
        """
        try:

            observer.on_next((self._media, self._candidate))
            observer.on_completed()

        except BaseException as e:
            observer.on_error(e)
