from dataclasses import dataclass
from datetime import datetime
from typing import List

from marshmallow import Schema, fields, EXCLUDE

from ..common.common import canonical_movie_title
from ..core import db, getLogger, JsonMixin
import banana.media

logger = getLogger(__name__)


class GenreSchema(Schema):
    id: int = fields.Integer(missing=None)
    name: str = fields.String(missing=None)
    genre_id: int = fields.String(missing=None)

    movie_match_candidate_id: int = fields.Integer(missing=None)
    movie_id: int = fields.String(missing=None)

    movie = fields.Inferred()
    movie_match_candidate = fields.Inferred()

    class Meta:
        exclude = ('movie_match_candidate', 'movie')


@dataclass
class Genre(db.Model, JsonMixin):
    """
    Genre model. Name is requires, genre_id is optional.
    """
    id: int = db.Column(db.Integer, primary_key=True)
    name: str = db.Column(db.String)
    genre_id: int = db.Column(db.Integer)

    movie_match_candidate_id: int = db.Column(db.Integer, db.ForeignKey('movie_match_candidate.id'), nullable=True)
    movie_id: int = db.Column(db.Integer, db.ForeignKey('movie.id'), nullable=True)

    def __hash__(self):
        return id(self)

    def transient_copy(self):
        return Genre(name=self.name,
                     genre_id=self.genre_id)

    @classmethod
    def schema(cls) -> Schema:
        return GenreSchema()


class MovieMatchCandidateSchema(Schema):
    id: int = fields.Integer(missing=None)

    title: str = fields.String(missing=None)
    original_title: str = fields.String(missing=None)
    release_year: int = fields.Integer(missing=None)
    plot: str = fields.String(missing=None)

    match: int = fields.Integer(missing=None)

    # metadata
    external_id: str = fields.String(missing=None)
    source: str = fields.String(missing=None)
    rating: str = fields.String(missing=None)
    poster: str = fields.String(missing=None)

    genres: List[Genre] = fields.Nested(nested=GenreSchema, missing=None, many=True)

    unmatched_item_id: int = fields.Integer(missing=None)

    class Meta:
        unknown = EXCLUDE


@dataclass
class MovieMatchCandidate(db.Model, JsonMixin):
    """
    Movie match candidate represents a match candidate for a given movie. This generally represents subset
    of common movie attributes for all sources: tmdb, imdb. Note howeer, that for some movies, only basic information
    is available. Treat all those fields as optional in the code. Don't have any assumptions that for a given movie we
    have anything other than a title.
    """
    id: int = db.Column(db.Integer, primary_key=True)

    title: str = db.Column(db.String)
    original_title: str = db.Column(db.String)
    release_year: int = db.Column(db.Integer)
    plot: str = db.Column(db.String)

    match: int = db.Column(db.Integer)

    # metadata
    external_id: str = db.Column(db.String)
    source: str = db.Column(db.String)
    rating: str = db.Column(db.String)
    poster: str = db.Column(db.String)

    genres: List[Genre] = db.relationship('Genre', cascade="all", lazy=True)

    unmatched_item_id: int = db.Column(db.Integer, db.ForeignKey('unmatched_item.id'),
                                       nullable=True)
    # transient field not stored in database
    akas = []

    def __hash__(self):
        return id(self)

    def canonical_title(self):
        return canonical_movie_title(self.title, self.release_year)

    def to_movie(self):
        return Movie(title=self.title,
                     original_title=self.original_title,
                     release_year=self.release_year,
                     plot=self.plot,
                     external_id=self.external_id,
                     rating=self.rating,
                     poster=self.poster,
                     genres=self.genres,
                     source=self.source)

    def transient_copy(self):
        return MovieMatchCandidate(
            title=self.title,
            original_title=self.original_title,
            release_year=self.release_year,
            plot=self.plot,
            match=self.match,
            external_id=self.external_id,
            source=self.source,
            rating=self.rating,
            poster=self.poster,
            genres=[g.transient_copy() for g in self.genres])

    @classmethod
    def schema(cls) -> Schema:
        return MovieMatchCandidateSchema()


class MovieSchema(Schema):
    id: int = fields.Integer(missing=None)

    title: str = fields.String(missing=None)
    original_title: str = fields.String(missing=None)
    release_year: int = fields.Integer(missing=None)
    plot: str = fields.String(missing=None)

    # metadata
    external_id: str = fields.String(missing=None)
    source: str = fields.String(missing=None)
    rating: str = fields.String(missing=None)
    poster: str = fields.String(missing=None)
    created_datetime: datetime = fields.DateTime(missing=None)

    genres: List[Genre] = fields.Nested(GenreSchema, many=True, missing=None)
    media_items: List['banana.media.item.ParsedMediaItem'] = fields.Nested('banana.media.item.ParsedMediaItemSchema',
                                                                           many=True, missing=None)


@dataclass
class Movie(db.Model, JsonMixin):
    id: int = db.Column(db.Integer, primary_key=True)

    title: str = db.Column(db.String)
    original_title: str = db.Column(db.String)
    release_year: int = db.Column(db.Integer)
    plot: str = db.Column(db.String)

    # metadata
    external_id: str = db.Column(db.String)
    source: str = db.Column(db.String)
    rating: str = db.Column(db.String)
    poster: str = db.Column(db.String)
    created_datetime: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    genres: List[Genre] = db.relationship('Genre', cascade="all", backref="movie", lazy=True)
    media_items: List['banana.media.item.ParsedMediaItem'] = db.relationship('banana.media.item.ParsedMediaItem',
                                                                             cascade="all", backref="matched_movie",
                                                                             lazy=True)

    def canonical_title(self):
        return canonical_movie_title(self.title, self.release_year)

    def transient_copy(self):
        return Movie(title=self.title,
                     original_title=self.original_title,
                     release_year=self.release_year,
                     plot=self.plot,
                     source=self.source,
                     external_id=self.external_id,
                     rating=self.rating,
                     poster=self.poster,
                     genres=[g.transient_copy() for g in self.genres])

    @staticmethod
    def from_match(movie_match_candidate):
        return movie_match_candidate.to_movie()

    @classmethod
    def schema(cls) -> Schema:
        return MovieSchema()


class MovieMatchRequestSchema(Schema):

    candidate = fields.Nested(MovieMatchCandidateSchema, required=True)
    media = fields.Nested('banana.media.item.ParsedMediaItemSchema', required=True)


@dataclass
class MovieMatchRequest(JsonMixin):

    candidate: MovieMatchCandidate
    media: 'banana.media.item.ParsedMediaItem'

    @classmethod
    def schema(cls):
        return MovieMatchRequestSchema()
