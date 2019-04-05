from datetime import datetime
from dataclasses import dataclass
from typing import List

from ..media.item import ParsedMediaItem
from ..movies.matchdecider import NonMatchReason
from ..movies.model import MovieMatchCandidate
from ..core import db
from ..common.json import json_serializable



@json_serializable
@dataclass
class UnmatchedItem(db.Model):
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
