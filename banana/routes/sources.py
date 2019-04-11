import json

from flask import request

from banana.common.json import _DateAwareJsonEncoder
from banana.core import app, getLogger
from banana.media.sources import get_media_source

logger = getLogger(__name__)


@app.route('/api/sources/<string:source>/search', methods=['GET'])
def source_search(source: str):
    title = request.args.get("title")
    results = get_media_source(source).search(title=title)
    logger.debug(results)
    return json.dumps(results, cls=_DateAwareJsonEncoder)
