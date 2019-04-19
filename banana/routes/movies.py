from flask import jsonify, request
from webargs.flaskparser import use_kwargs

from ..core.filtering import PageWithOrderSchema, with_filters, paginated, using_attributes
from ..core import app, getLogger
from ..media.item import ParsedMediaItem
from ..media.sources import get_media_source
from ..movies.model import Movie

logger = getLogger(__name__)

DEFAULT_ITEMS_PER_PAGE = 5


def _order_spec(order_by, order_direction):
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


@app.route("/api/movies/<int:movie_id>", methods=['GET'])
def movies_get(movie_id):
    return jsonify(Movie.query.filter_by(id=movie_id).first_or_404())


@app.route("/api/movies", methods=["GET"])
@use_kwargs(PageWithOrderSchema.with_page_size(5), locations=('query',))
def movies_list(page, page_size, order_by, order_direction):

    query = Movie.query.join(ParsedMediaItem).with_filters(request.query_string, using_attributes(
        job_id=ParsedMediaItem.job_id,
        title=ParsedMediaItem.title,
    )).order_by(_order_spec(order_by, order_direction))

    return jsonify(paginated(query.paginate(page, page_size, False)))


@app.route("/api/movies/count", methods=['GET'])
def movies_count():
    query = Movie.query.join(ParsedMediaItem).with_filters(request.query_string, using_attributes(
        job_id=ParsedMediaItem.job_id
    ))
    return jsonify(total_items=query.count())


@app.route("/api/movies/<int:id>/cast", methods=['GET'])
def movies_people(id):
    source = get_media_source('tmdb')
    return jsonify(source.movie_top3_cast(id))


@app.route("/api/movies/sources/<string:source>/<source_id>", methods=['GET'])
def movies_from_source(source, source_id):
    match_candidate = get_media_source(source).get_by_id(source_id)
    logger.debug(match_candidate)
    return jsonify(match_candidate)
