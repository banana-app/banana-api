import json

from flask import request, Response

from banana.media.jobs import ManualMovieMatchJob, FixMatchJob
from banana.movies.model import MovieMatchRequest
from ..media.item import ParsedMediaItem
from ..core import getLogger, app, ThreadPoolJobExecutor

from ..common.json import _DateAwareJsonEncoder

logger = getLogger(__name__)


@app.route('/api/media/<int:media_id>', methods=['GET'])
def get_media(media_id: int):
    media = ParsedMediaItem.query.filter_by(id=media_id).first_or_404()
    return json.dumps(media, cls=_DateAwareJsonEncoder)


@app.route('/api/media/<int:media_id>', methods=['POST'])
def update_media(media_id: int):
    logger.info("Fix match request: {}".format(request.data))

    match_request = MovieMatchRequest.from_json(request.data)
    ThreadPoolJobExecutor().submit(FixMatchJob(match_request=match_request, media_id=media_id))
    return Response(status=202)
