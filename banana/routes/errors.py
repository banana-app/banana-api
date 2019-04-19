import traceback

from flask import jsonify
from werkzeug.exceptions import HTTPException, BadRequest
from marshmallow.validate import ValidationError

from ..core import app, getLogger

logger = getLogger(__name__)


@app.errorhandler(BaseException)
def error(exception):
    code = 500
    if isinstance(exception, HTTPException):
        code = exception.code
    elif isinstance(exception, ValidationError):
        code = BadRequest.code
    else:
        logger.error(f'Uncaught application exception: {traceback.format_exc()}. Returning Internal Server Error.')
    return jsonify(error={'message': str(exception)}), code
