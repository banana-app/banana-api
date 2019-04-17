from flask import jsonify
from marshmallow import fields
from webargs.flaskparser import use_kwargs

from banana.core import app, getLogger
from banana.media.sources import get_media_source

logger = getLogger(__name__)


@app.route('/api/sources/<string:source>/search', methods=['GET'])
@use_kwargs({'title': fields.String(required=True)})
def source_search(source: str, title: str):
    results = get_media_source(source).search(title=title)
    logger.debug(results)
    return jsonify(results)
