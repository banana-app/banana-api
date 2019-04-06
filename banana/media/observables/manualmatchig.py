import rx
from funcy import any
from whatever import _

from banana.core import JobContext, getLogger
from banana.media.model import UnmatchedItem
from banana.media.sources import get_media_source
from banana.movies.model import MovieMatchRequest


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
                 match_request: MovieMatchRequest,
                 source_factory=get_media_source):
        super().__init__()
        self._job_context = job_context
        self.logger = getLogger(self.__class__.__name__)
        self._match_request = match_request
        self._get_media_source = source_factory

    def __call__(self, observer: rx.Observer):
        """
        It emits an event to the observers with UnmatchedItem and movie match candidate to match with that item.
        :param observer - an Observer to handle actual match.
        """
        try:
            if any(_ == self._match_request.match_type, ['imdb', 'tmdb', 'local']):
                unmatched = UnmatchedItem.query.filter_by(id=self._match_request.unmatched_item_id).one_or_none()
                candidate = self._get_media_source(self._match_request.match_type).get_by_id(
                    self._match_request.match_type_id)

                observer.on_next((unmatched, candidate))
                observer.on_completed()

            else:
                observer.on_error(f'Unknown match request type: {self._match_request}')

        except BaseException as e:
            observer.on_error(e)
