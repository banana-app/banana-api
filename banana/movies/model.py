import datetime
from dataclasses import dataclass
from typing import List

from ..media.item import ParsedMediaItem
from ..core import db, getLogger
from ..common.common import canonical_movie_title
from ..common.json import json_serializable

logger = getLogger(__name__)


@json_serializable
@dataclass
class MovieMatchRequest(object):
    """
    Movie match request. A python representation of match request from UI, for a given movie candidate.

    Supported match types:
    * imdb - match based on IMDB id; match_type_id is IMDB id in this case
    * tmdb - match based on TMDB id; match_type_id is TMDB id in this case
    * local - match against pre-exsiting match candidates, match_type_id is local MovieMatchCandidate id
    * custom - custom match - cutom_name and custom_year is required
    """
    unmatched_item_id: int = None
    # local|tmdb|imdb|cutom
    match_type: str = None
    match_type_id: str = None

    custom_name: str = None
    custom_year: str = None


@json_serializable
@dataclass
class Genre(db.Model):
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


@json_serializable
@dataclass
class MovieMatchCandidate(db.Model):
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
    external_id: int = db.Column(db.String)
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


@json_serializable
@dataclass
class Movie(db.Model):
    id: int = db.Column(db.Integer, primary_key=True)

    title: str = db.Column(db.String)
    original_title: str = db.Column(db.String)
    release_year: int = db.Column(db.Integer)
    plot: str = db.Column(db.String)

    # metadata
    external_id: int = db.Column(db.String)
    source: str = db.Column(db.String)
    rating: str = db.Column(db.String)
    poster: str = db.Column(db.String)
    created_datetime: datetime = db.Column(db.DateTime, default=datetime.datetime.utcnow)

    genres: List[Genre] = db.relationship('Genre', cascade="all", backref="movie", lazy=True)
    media_items: List[ParsedMediaItem] = db.relationship("ParsedMediaItem", cascade="all", backref="matched_movie",
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
