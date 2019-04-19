from flask import request, jsonify
from webargs.flaskparser import use_kwargs

from banana.media.jobs import GenericSyncJob
from ..core.filtering import PageWithOrderSchema, paginated, using_attributes
from ..core import getLogger, app, db, SimpleJobExecutor
from ..media.item import ParsedMediaItem

logger = getLogger(__name__)


_query_mapping = {
    'unmatched': ParsedMediaItem.unmatched,
    'ignored': ParsedMediaItem.ignored,
    'filename': ParsedMediaItem.filename
}


def _order_spec(order_by, order_direction):
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


@app.route('/api/media/<int:media_id>', methods=['GET'])
def get_media(media_id: int):
    media = ParsedMediaItem.query.filter_by(id=media_id).first_or_404()
    return jsonify(media)


@app.route('/api/media', methods=['PUT'])
def update_media():
    logger.info(f'Update media request: {request.data}')

    updated = ParsedMediaItem.from_json(request.data, many=True)

    def update():
        for i in updated:
            db.session.merge(i)

        db.session.commit()

    SimpleJobExecutor().submit(GenericSyncJob.from_callable(update))

    return '', 200


@app.route('/api/media', methods=['GET'])
@use_kwargs(PageWithOrderSchema.with_page_size(10), locations=('query',))
def list_media(page, page_size, order_by, order_direction):
    query = ParsedMediaItem.query.with_filters(request.query_string, _query_mapping)\
        .order_by(_order_spec(order_by, order_direction))

    return jsonify(paginated(query.paginate(page, page_size, False)))


@app.route('/api/media/count', methods=['GET'])
def media_count():
    query = ParsedMediaItem.query.with_filters(request.query_string, _query_mapping)

    return jsonify(total_items=query.count())
