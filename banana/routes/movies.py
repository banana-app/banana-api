import json

from flask import request, Response
from sqlalchemy.orm import joinedload
from sqlalchemy import or_

from banana.common.json import _DateAwareJsonEncoder
from banana.core import app
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
    ThreadPoolJobExecutor().submit(ManualMovieMatchJob(match_request=match_request))
    return Response(status=202)


@app.route("/api/movies/<int:movie_id>")
def get_movie(movie_id):
    movie = Movie.query.options(joinedload("*")).filter(Movie.id == movie_id).first()
    return json.dumps(movie, cls=_DateAwareJsonEncoder)


@app.route("/api/movies", methods=["GET"])
def movies():
    page = request.args.get("page")
    order_by=request.args.get("order_by")
    order_direction=request.args.get("order_direction")
    if not page:
        total = Movie.query.count()
        items = Movie.query.options(joinedload('*')).all()
        return json.dumps({"total_items": total,
                           "pages": total_pages(len(items), items_per_page),
                           "items": items}, cls=_DateAwareJsonEncoder)
    else:
        try:
            int_page = int(page)
        except ValueError:
            raise ValueError("Invalid value for 'page' query parameter: {}. Should be an integer value.".format(page))
        query = Movie.query.options(joinedload("*"))
        if order_by is not None and order_direction is not None:
            query = query.order_by("{} {}".format(order_by, order_direction))
        results = query.paginate(int_page, items_per_page, False)
        return json.dumps({"total_items": results.total, "pages": total_pages(results.total, items_per_page),
                           "items": results.items}, cls=_DateAwareJsonEncoder)


def local_search(title):

    total_results = Movie.query.filter(or_(
        Movie.title.like(f'%{title}%'),
        Movie.original_title.like(f'%{title}%')
    )).count()

    movies = Movie.query.filter(or_(
        Movie.title.like(f'%{title}%'),
        Movie.original_title.like(f'%{title}%')
    )).limit(3)

    results = []
    for m in movies:
        results.append({
            "title": m.title,
            "original_title": m.original_title,
            "poster": m.poster,
            "plot": m.plot,
            "release_year": m.release_year,
            "source_id": m.id,
            "source": "local"
        })

    return total_results, results


@app.route("/api/movies/search/local", methods=["GET"])
def movies_search_local():
    total_results, results = local_search(request.args.get('title'))

    return json.dumps({'total_results': total_results, 'results': results}, cls=_DateAwareJsonEncoder)


@app.route("/api/movies/search", methods=["GET"])
def movies_search():
    title = request.args.get("title")
    for_item = request.args.get("for_item")
    source = request.args.get("source", "tmdb")

    results = []

    if source == "local":
        _, results = local_search(title=title)
    else:
        results = get_media_source(source).search(title=title)
        if for_item:
            for r in results:
                r["unmatched_item_id"] = for_item

    logger.debug(results)
    return json.dumps(results, cls=_DateAwareJsonEncoder)


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
