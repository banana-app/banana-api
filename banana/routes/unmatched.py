from flask import request, jsonify
from funcy import some
from marshmallow import fields
from webargs.flaskparser import use_kwargs
from whatever import _

from ..common.common import total_pages
from ..core import app
from ..media.item import ParsedMediaItem
from ..media.model import UnmatchedItem

ITEMS_PER_PAGE = 10


@app.route("/api/media/search", methods=["GET"])
@use_kwargs({'term': fields.String(required=True)}, locations=('query',))
def media_search(term):

    criteria = ParsedMediaItem.filename.like(f'%{term}%')
    total_results = ParsedMediaItem.query.filter(criteria).count()
    media = ParsedMediaItem.query.filter(criteria).limit(3).all()

    return jsonify(total_results=total_results, results=media)


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
@use_kwargs({
    'page': fields.Integer(missing=1),
    'per_page': fields.Integer(missing=ITEMS_PER_PAGE),
    'order_by': fields.String(missing=None),
    'order_direction': fields.String(missing=None),
})
def list_unmatched(page, per_page, order_by, order_direction):

    include_ignored = some(_ == 'include_ignored', request.args)

    query = UnmatchedItem.query.join(ParsedMediaItem)

    if order_by is not None and order_direction is not None:
        order_clause = _order_by_builder(order_by, order_direction)
        query = query.order_by(order_clause)

    if not include_ignored:
        query = query.filter(ParsedMediaItem.ignored.isnot(True))

    results = query.paginate(page, per_page, False)

    return jsonify(total_items=results.total,
                   pages=total_pages(results.total, per_page),
                   items=results.items, many=True)


@app.route("/api/unmatched/count")
def unmatched_count():
    total_items = UnmatchedItem.query.count()
    return jsonify(total_items=total_items)


@app.route("/api/unmatched/<int:unmatched_item_id>/<file>", methods=["GET"])
def get_unmatched(file, unmatched_item_id):
    return jsonify(UnmatchedItem.query.filter_by(id=unmatched_item_id).first_or_404())
