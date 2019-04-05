from flask import request
from banana.core import app
import banana.common
from banana.common.json import _DateAwareJsonEncoder
from sqlalchemy.orm import joinedload

from banana.media.item import ParsedMediaItem
from banana.media.model import UnmatchedItem
import json

items_per_page = 10


@app.route("/api/media/search", methods=["GET"])
def media_searchbla():
    title = request.args.get("term")

    results = []
    media = ParsedMediaItem.query.filter(ParsedMediaItem.filename.like("%" + title + "%")).limit(5)

    results = []
    for m in media:
        results.append({
            "filename": m.filename,
            "id": m.id,
            "matched_to": m.matched_movie_id
        })
    return json.dumps(results, cls=_DateAwareJsonEncoder)


@app.route("/api/unmatched", methods=["GET"])
def list_unmatched():
    page = request.args.get("page")
    if not page:
        total = UnmatchedItem.query.count()
        items = UnmatchedItem.query.options(joinedload('*')).all()
        return json.dumps({"total_items": total,
                           "pages": banana.common.total_pages(len(items), items_per_page),
                           "items": items}, cls=_DateAwareJsonEncoder)
    else:
        try:
            int_page = int(page)
        except ValueError:
            raise ValueError("Invalid value for 'page' query parameter: {}. Should be an integer value.".format(page))

        results = UnmatchedItem.query.options(joinedload("*")).paginate(int_page, items_per_page, False)
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
