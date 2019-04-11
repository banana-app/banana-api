import json

from flask import request
from sqlalchemy.orm import joinedload

from banana.common.json import _DateAwareJsonEncoder
from banana.core import app
from banana.media.item import ParsedMediaItem
from banana.media.jobs import ManualMovieMatchJob
from ..common.common import total_pages
from ..core import getLogger, ThreadPoolJobExecutor
from ..media.sources import get_media_source
from ..movies.model import Movie, MovieMatchRequest

logger = getLogger(__name__)


items_per_page = 5


@app.route("/api/movies", methods=["POST"])
def movies_match():
    logger.info("Matching request: {}".format(request.data))
    match_request = MovieMatchRequest.from_json(request.data)
    match_job = ManualMovieMatchJob(match_request=match_request)
    ThreadPoolJobExecutor().submit(match_job)
    return json.dumps({'job_id': match_job.id()})


@app.route("/api/movies/<int:movie_id>")
def get_movie(movie_id):
    movie = Movie.query.options(joinedload("*")).filter(Movie.id == movie_id).first()
    return json.dumps(movie, cls=_DateAwareJsonEncoder)


@app.route("/api/movies", methods=["GET"])
def movies():
    page = request.args.get("page")
    order_by=request.args.get("order_by")
    order_direction=request.args.get("order_direction")
    job_id=request.args.get("job_id")

    if not page:
        query = Movie.query.options(joinedload('*'))

        if job_id is not None:
            query = query.join(ParsedMediaItem).filter(ParsedMediaItem.job_id == job_id)

        total = query.count()
        items = query.all()

        return json.dumps({"total_items": total,
                           "pages": total_pages(len(items), items_per_page),
                           "items": items}, cls=_DateAwareJsonEncoder)
    else:
        try:
            int_page = int(page)
        except ValueError:
            raise ValueError("Invalid value for 'page' query parameter: {}. Should be an integer value.".format(page))

        query = Movie.query.options(joinedload("*"))

        if job_id is not None:
            query = query.join(ParsedMediaItem).filter(ParsedMediaItem.job_id == job_id)

        if order_by is not None and order_direction is not None:
            query = query.order_by(f"{order_by} {order_direction}")

        results = query.paginate(int_page, items_per_page, False)

        return json.dumps({"total_items": results.total, "pages": total_pages(results.total, items_per_page),
                           "items": results.items}, cls=_DateAwareJsonEncoder)


@app.route("/api/movies/count")
def movies_count():
    total = Movie.query.count()
    return json.dumps({"total_items": total})


@app.route("/api/movies/<int:id>/cast")
def movies_people(id):
    source = get_media_source("tmdb")
    return json.dumps(source.movie_top3_cast(id))


@app.route("/api/movies/sources/<string:source>/<source_id>")
def movies_from_source(source, source_id):
    media_source = get_media_source(source)
    match_candidate = media_source.get_by_id(source_id)
    logger.debug(match_candidate)
    return json.dumps(match_candidate, cls=_DateAwareJsonEncoder)
