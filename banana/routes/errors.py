from ..core import app, getLogger
from flask import jsonify
import traceback
import sys

logger = getLogger(__name__)


@app.errorhandler(Exception)
def error(exception):
    logger.error("Uncaught exception: {}".format(exception))
    traceback.print_exc(file=sys.stdout)
    return jsonify({"error": {"message": str(exception)}}), 500
