from gevent import monkey
monkey.patch_all()
from flask import jsonify

from banana.events import JobCompletedEvent
from banana.routes.movies import *
from banana.routes.unmatched import *
from banana.routes.media import *
from banana.routes.sources import *

from banana.core import app, db, socket, getLogger

from banana.core.jobs import ThreadPoolJobExecutor, AsyncIOJobExecutor
from banana.media.jobs import FileSystemScanJob, JobTypes

logger = getLogger(__name__)

db.create_all()


def process_movies():
    ThreadPoolJobExecutor().submit(FileSystemScanJob())


@app.route('/api/scans')
def scans():
    process_movies()
    return jsonify({"status": "OK"})


@socket.on('connect', namespace='/sync')
def jobs():
    logger.info("Socket connected to /sync endpoint")


@app.route('/api/ping')
def ping():

    event = JobCompletedEvent(job_id='1234', job_type=JobTypes.MANUAL_MATCH.value)
    socket.emit(JobTypes.MANUAL_MATCH.value, event.to_json(), namespace='/jobs')
    logger.debug("Emitting JobCompletedEvent with message type '{}' and namespace {}; {}"
                      .format(JobTypes.MANUAL_MATCH, '/jobs', event.to_json()))
    logger.info("Pinging with: {}".format(event))
    return jsonify({"status": "ok"})


if __name__ == '__main__':
    socket.run(app)
