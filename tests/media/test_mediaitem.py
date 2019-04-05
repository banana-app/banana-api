import unittest
from banana.core import app, db
from banana.movies.model import *
from banana.media.item import ParsedMediaItem
from banana.media.model import *
from pathlib import PurePath


class ParsedMediaItemTest(unittest.TestCase):

    def setUp(self):
        self.app = app
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///'
        self.db = db
        self.db.drop_all()
        self.db.create_all()

    def test_media_item_already_matched(self):
        movie = Movie(title="Foo")
        movie.media_items += [ParsedMediaItem(filename="Foo", path="bar")]
        self.db.session.add(movie)
        self.db.session.commit()

        self.assertEqual("Foo", ParsedMediaItem(filename="Foo", path="bar").already_matched().filename)

    def test_empty_media_item_already_matched(self):
        self.assertEqual(None, ParsedMediaItem().already_matched())

    def test_media_item_not_matched(self):
        self.db.session.add(ParsedMediaItem(filename="Foo", path="bar"))
        self.db.session.commit()
        self.assertEqual(None, ParsedMediaItem(filename="Foo", path="bar").already_matched())

    def test_absolute_path(self):
        item_abs_path1 = ParsedMediaItem(path='/foo/bar',
                                     filename='The Awesome Movie.mkv').absolute_path()
        item_abs_path2 = ParsedMediaItem().absolute_path()
        item_abs_path3 = ParsedMediaItem(target_path='/qoox/', target_filename='Westing Boom.mp4')\
            .absolute_target_path()
        self.assertEqual('/foo/bar/The Awesome Movie.mkv', PurePath(item_abs_path1).as_posix())
        self.assertEqual(None, item_abs_path2)
        self.assertEqual('/qoox/Westing Boom.mp4', PurePath(item_abs_path3).as_posix())

