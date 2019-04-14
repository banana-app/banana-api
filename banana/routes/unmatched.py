from flask import request
from banana.core import app
import banana.common
from banana.common.json import _DateAwareJsonEncoder
from sqlalchemy.orm import joinedload

from banana.media.item import ParsedMediaItem
from banana.media.model import UnmatchedItem
import json

from funcy import some
from whatever import _

items_per_page = 10


@app.route("/api/media/search", methods=["GET"])
def media_searchbla():
    title = request.args.get("term")

    results = []
    total_results = ParsedMediaItem.query.filter(ParsedMediaItem.filename.like("%" + title + "%")).count()
    media = ParsedMediaItem.query.filter(ParsedMediaItem.filename.like("%" + title + "%")).limit(3).all()

    return json.dumps({'total_results': total_results, 'results': media}, cls=_DateAwareJsonEncoder)


def _order_by_builder(order_by, order_direction):
    _mapping = {
        'created_datetime': {
            'desc': ParsedMediaItem.created_datetime.desc(),
            'asc': ParsedMediaItem.created_datetime.asc()
        },
        'filename': {
            'desc': ParsedMediaItem.filename.desc(),
            'asc': ParsedMediaItem.filename.asc()
        }
    }
    return _mapping[order_by][order_direction]


@app.route("/api/unmatched", methods=["GET"])
def list_unmatched():
    page = request.args.get("page", 200)
    order_by = request.args.get("order_by")
    order_direction = request.args.get("order_direction")
    include_ignored = some(_ == 'include_ignored', request.args)

    try:
        int_page = int(page)
    except ValueError:
        raise ValueError("Invalid value for 'page' query parameter: {}. Should be an integer value.".format(page))

    query = UnmatchedItem.query.options(joinedload("*")).join(ParsedMediaItem)

    if order_by is not None and order_direction is not None:
        order_clause = _order_by_builder(order_by, order_direction)
        query = query.order_by(order_clause)

    if not include_ignored:
        query = query.filter(ParsedMediaItem.ignored.isnot(True))

    results = query.paginate(int_page, items_per_page, False)
    return json.dumps(
        {"total_items": results.total, "pages": banana.common.total_pages(results.total, items_per_page),
         "items": results.items}, cls=_DateAwareJsonEncoder)


@app.route("/api/unmatched/count")
def unmatched_count():
    total_items = UnmatchedItem.query.count()
    return json.dumps({"total_items": total_items})


@app.route("/api/unmatched/<int:unmatched_item_id>/<file>", methods=["GET"])
def get_unmatched(file, unmatched_item_id):
    return json.dumps(UnmatchedItem
                      .query.options(joinedload('*'))
                      .filter(UnmatchedItem.id == unmatched_item_id).first(), cls=_DateAwareJsonEncoder)
