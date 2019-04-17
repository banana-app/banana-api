from flask import request, jsonify
from marshmallow import Schema, fields
from webargs.flaskparser import use_kwargs

from ..core import app, getLogger, ThreadPoolJobExecutor
from ..media.item import ParsedMediaItem
from ..media.jobs import ManualMovieMatchJob
from ..common.common import total_pages
from ..media.sources import get_media_source
from ..movies.model import Movie, MovieMatchRequest

logger = getLogger(__name__)

DEFAULT_ITEMS_PER_PAGE = 5


@app.route("/api/movies", methods=["POST"])
def movies_match():
    logger.info(f'Matching request: {request.data}')

    match_request = MovieMatchRequest.from_json(request.data)
    match_job = ManualMovieMatchJob(match_request=match_request)
    ThreadPoolJobExecutor().submit(match_job)

    return jsonify(job_id=match_job.id())


@app.route("/api/movies/<int:movie_id>", methods=['GET'])
def get_movies(movie_id):
    return jsonify(Movie.query.filter_by(id=movie_id).first_or_404())


def _order_by_builder(order_by, order_direction):
    _mapping = {
        'created_datetime': {
            'desc': Movie.created_datetime.desc(),
            'asc': Movie.created_datetime.asc()
        },
        'title': {
            'desc': Movie.title.desc(),
            'asc': Movie.title.asc()
        }
    }
    return _mapping[order_by][order_direction]


class MoviesArgsSchema(Schema):
    page = fields.Integer(missing=1)
    page_size = fields.Integer(missing=DEFAULT_ITEMS_PER_PAGE)
    order_by = fields.String(missing='created_datetime')
    order_direction = fields.String(missing='desc')
    job_id = fields.String(missing=None)


@app.route("/api/movies", methods=["GET"])
@use_kwargs(MoviesArgsSchema(), locations=('query',))
def movies(page, page_size, order_by, order_direction, job_id):

    query = Movie.query

    if order_by is not None and order_direction is not None:
        order_clause = _order_by_builder(order_by, order_direction)
        query = query.order_by(order_clause)

    if job_id is not None:
        query = query.join(ParsedMediaItem).filter(ParsedMediaItem.job_id == job_id)

    results = query.paginate(page, page_size, False)

    return jsonify(total_items=results.total,
                   pages=total_pages(results.total, page_size),
                   items=results.items)


@app.route("/api/movies/count", methods=['GET'])
def movies_count():
    total = Movie.query.count()
    return jsonify(total_items=total)


@app.route("/api/movies/<int:id>/cast", methods=['GET'])
def movies_people(id):
    source = get_media_source('tmdb')
    return jsonify(source.movie_top3_cast(id))


@app.route("/api/movies/sources/<string:source>/<source_id>", methods=['GET'])
def movies_from_source(source, source_id):
    match_candidate = get_media_source(source).get_by_id(source_id)
    logger.debug(match_candidate)
    return jsonify(match_candidate)
