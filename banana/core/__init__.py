import logging
import logging.config
import os.path

import dacite
from flask import Flask
from flask.json import JSONEncoder
from flask_socketio import SocketIO
from flask_sqlalchemy import SQLAlchemy

from .jobs import *


class BananaJSONEncoder(JSONEncoder):

    def default(self, o):

        if hasattr(o, 'schema'):
            return o.schema().dump(o)
        else:
            return JSONEncoder.default(self, o)


app = Flask(__name__)
app.json_encoder = BananaJSONEncoder

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


class JsonMixin:
    """
    A JSON serialization and deserialization mixin for classes. It assumes that supporting class
    has already defined a class method 'def schema() -> Schema` returning marshmallow schema, which is
    then used for serialization/deserialization.
    """

    def to_json(self):
        return self.__class__.schema().dumps(self)

    @classmethod
    def from_json(cls, serialized, many=False):
        if many:
            items = cls.schema().loads(serialized, many=True)
            return [dacite.from_dict(data_class=cls, data=a, config=dacite.Config(check_types=False)) for a in items]
        else:
            return dacite.from_dict(data_class=cls,
                                    data=cls.schema().loads(serialized),
                                    config=dacite.Config(check_types=False))
