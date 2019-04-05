import logging
import logging.config
import os.path

from flask import Flask
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from .jobs import *


app = Flask(__name__)

config = os.path.abspath(
    os.path.join(app.root_path, '..', '..', 'config', os.environ.get('FLASK_ENV', 'development').lower() + ".json"))
app.config.from_json(config)

db = SQLAlchemy(app)
socket = SocketIO(app)


def tbdb_api_key() -> str:
    return os.environ.get('TMDB_API_KEY')


class Config(object):

    @classmethod
    def movies_target_path(cls) -> str:
        return app.config['BANANA_MEDIA_MOVIES_TARGET_PATH']

    @classmethod
    def threshold(cls) -> int:
        return int(app.config.get('BANANA_MATCHER_THRESHOLD', 90))

    @classmethod
    def media_movie_pattern_name(cls) -> str:
        return app.config.get('BANANA_MEDIA_MOVIE_PATTERN_NAME')

    @classmethod
    def media_movies_target_path(cls) -> str:
        return app.config.get('BANANA_MEDIA_MOVIES_TARGET_PATH')

    @classmethod
    def media_scanner_skip_filetype_checks(cls):
        return app.config.get('BANANA_MEDIA_SCANNER_SKIP_FILETYPE_CHECKS')

    @classmethod
    def media_matcher(cls) -> str:
        return app.config.get('BANANA_MEDIA_MATCHER')

    @classmethod
    def media_target_resolver(cls) -> str:
        return app.config.get('BANANA_MEDIA_TARGET_RESOLVER')

    @classmethod
    def media_target(cls) -> str:
        return app.config.get('BANANA_MEDIA_TARGET')

    @classmethod
    def media_scan_path(cls):
        return app.config.get('BANANA_MEDIA_SCAN_PATH')


logging.config.fileConfig(os.path.abspath(
    os.path.join(app.root_path, '..', '..', 'config', 'logging.conf')))


def getLogger(name):
    """
    Returns logger. This is just shorthand for python logging.
    :param name: a Logger name
    :return: logger
    """
    return logging.getLogger(name)
