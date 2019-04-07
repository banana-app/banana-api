import json
from ..media.item import ParsedMediaItem
from ..core import getLogger, app

from ..common.json import _DateAwareJsonEncoder

logger = getLogger(__name__)


@app.route('/api/media/<int:media_id>', methods=['GET'])
def get_media(media_id: int):
    media = ParsedMediaItem.query.filter_by(id=media_id).first_or_404()
    return json.dumps(media, cls=_DateAwareJsonEncoder)
