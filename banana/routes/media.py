from flask import request, jsonify

from ..core import getLogger, app, db, ThreadPoolJobExecutor
from ..media.item import ParsedMediaItem
from ..media.jobs import FixMatchJob
from ..movies.model import MovieMatchRequest

logger = getLogger(__name__)


@app.route('/api/media/<int:media_id>', methods=['GET'])
def get_media(media_id: int):
    media = ParsedMediaItem.query.filter_by(id=media_id).first_or_404()
    return jsonify(media)


@app.route('/api/media/<int:media_id>', methods=['POST'])
def match_media(media_id: int):
    logger.info(f'Fix match request: {request.data}')

    match_request = MovieMatchRequest.from_json(request.data)
    fix_match_job = FixMatchJob(match_request=match_request, media_id=media_id)
    ThreadPoolJobExecutor().submit(fix_match_job)

    return jsonify(job_id=fix_match_job.id())


@app.route('/api/media', methods=['PUT'])
def update_media():
    logger.info(f'Update media request: {request.data}')

    updated = ParsedMediaItem.from_json(request.data, many=True)
    for i in updated:
        db.session.merge(i)

    db.session.commit()

    return '', 200

