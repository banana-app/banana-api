from flask import request, jsonify

from ..media.jobs import ManualMovieMatchJob, FixMatchJob
from ..movies.model import MovieMatchRequest
from ..core import app, ThreadPoolJobExecutor, getLogger

logger = getLogger(__name__)


@app.route('/api/matches', methods=['POST'])
def create_match():

    logger.info(f'Creating match: {request.data}')
    match_request = MovieMatchRequest.from_json(request.data)
    executor = ThreadPoolJobExecutor()

    if match_request.media.already_matched():
        match_job = FixMatchJob(media=match_request.media, candidate=match_request.candidate)
    else:
        match_job = ManualMovieMatchJob(media=match_request.media, candidate=match_request.candidate)

    executor.submit(match_job)

    return jsonify(job_id=match_job.id())
