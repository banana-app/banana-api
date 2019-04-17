from dataclasses import dataclass
from datetime import datetime
from typing import List

from marshmallow import Schema, fields, EXCLUDE
from marshmallow_enum import EnumField

from ..core import db, JsonMixin
from ..media.item import ParsedMediaItem, ParsedMediaItemSchema
from ..movies.matchdecider import NonMatchReason
from ..movies.model import MovieMatchCandidate, MovieMatchCandidateSchema


class UnmatchedItemSchema(Schema):

    id: int = fields.Integer(missing=None)
    potential_matches: List[MovieMatchCandidate] = fields.Nested(nested=MovieMatchCandidateSchema, many=True)
    parsed_media_item: ParsedMediaItem = fields.Nested(nested=ParsedMediaItemSchema, missing=None)

    created_datetime: datetime = fields.DateTime(missing=None)
    non_match_reason: NonMatchReason = EnumField(NonMatchReason)

    class Meta:
        unknown = EXCLUDE


@dataclass
class UnmatchedItem(db.Model, JsonMixin):
    """
    Stores the result of unsuccessful match. Potential matches are the list we tried to match media item against.
    Additionally it keeps NonMatchReason enum (matches below threshold, we have multiple candidates with the same
    threshold.
    """
    id: int = db.Column(db.Integer, primary_key=True)
    potential_matches: List[MovieMatchCandidate] = db.relationship('MovieMatchCandidate', backref='unmatched_item',
                                                                   cascade="all", lazy=True,
                                                                   order_by="desc(MovieMatchCandidate.match)")
    parsed_media_item: ParsedMediaItem = db.relationship('ParsedMediaItem', backref='unmatched_item',
                                                         cascade="all", lazy=True, uselist=False)
    created_datetime: datetime = db.Column(db.DateTime, default=datetime.utcnow)
    non_match_reason: NonMatchReason = db.Column(db.Enum(NonMatchReason))

    @classmethod
    def schema(cls) -> Schema:
        return UnmatchedItemSchema()
