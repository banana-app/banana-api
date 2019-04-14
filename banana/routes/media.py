import json

from flask import request

from banana.media.jobs import FixMatchJob
from banana.movies.model import MovieMatchRequest
from ..media.item import ParsedMediaItem
from ..core import getLogger, app, db, ThreadPoolJobExecutor

from ..common.json import _DateAwareJsonEncoder

logger = getLogger(__name__)


@app.route('/api/media/<int:media_id>', methods=['GET'])
def get_media(media_id: int):
    media = ParsedMediaItem.query.filter_by(id=media_id).first_or_404()
    return json.dumps(media, cls=_DateAwareJsonEncoder)


@app.route('/api/media/<int:media_id>', methods=['POST'])
def update_media(media_id: int):
    logger.info(f'Fix match request: {request.data}')
    match_request = MovieMatchRequest.from_json(request.data)
    fix_match_job = FixMatchJob(match_request=match_request, media_id=media_id)
    ThreadPoolJobExecutor().submit(fix_match_job)
    return json.dumps({'job_id': fix_match_job.id()})


@app.route('/api/media', methods=['PUT'])
def ignore_media():
    logger.info(f'Ignore media request: {request.data}')
    ignored = json.loads(request.data)

    for i in ignored:
        ParsedMediaItem.query.filter_by(id=i.get('id')).update({ParsedMediaItem.ignored: i.get('ignored')})

    db.session.commit()

    return '', 200

