import os
from dataclasses import dataclass
from datetime import datetime

from marshmallow import Schema, fields, EXCLUDE
from sqlalchemy import and_

from banana.core import db, JsonMixin
from banana.media.model import UnmatchedItem, UnmatchedItemSchema


class ParsedMediaItemSchema(Schema):

    id: int = fields.Int(required=True)
    filename: str = fields.String(missing=None)
    target_filename: str = fields.String(missing=None)
    path: str = fields.String(missing=None)
    target_path: str = fields.String(missing=None)
    audio: str = fields.String(missing=None)
    codec: str = fields.String(missing=None)
    container: str = fields.String(missing=None)
    episode: str = fields.String(missing=None)
    episodeName: str = fields.String(missing=None)
    garbage: str = fields.String(missing=None)
    group: str = fields.String(missing=None)
    hardcoded: str = fields.String(missing=None)
    language: str = fields.String(missing=None)
    proper: str = fields.String(missing=None)
    quality: str = fields.String(missing=None)
    region: str = fields.String(missing=None)
    repack: str = fields.String(missing=None)
    resolution: str = fields.String(missing=None)
    season: str = fields.String(missing=None)
    title: str = fields.String(missing=None)
    website: str = fields.String(missing=None)
    widescreen: str = fields.String(missing=None)
    year: str = fields.String(missing=None)

    job_id: str = fields.String(missing=None)
    ignored: bool = fields.Boolean(missing=None)

    created_datetime: datetime = fields.DateTime(missing=None)

    unmatched = fields.Nested(UnmatchedItemSchema, missing=None)

    # reference to matched movie, if this media is already matched to a movie
    matched_movie_id: int = fields.Integer(missing=None)

    class Meta:
        unknown = EXCLUDE


@dataclass
class ParsedMediaItem(db.Model, JsonMixin):
    id: int = db.Column(db.Integer, primary_key=True)
    filename: str = db.Column(db.String)
    target_filename: str = db.Column(db.String)
    path: str = db.Column(db.String)
    target_path: str = db.Column(db.String)
    audio: str = db.Column(db.String)
    codec: str = db.Column(db.String)
    container: str = db.Column(db.String)
    episode: str = db.Column(db.String)
    episodeName: str = db.Column(db.String)
    garbage: str = db.Column(db.String)
    group: str = db.Column(db.String)
    hardcoded: str = db.Column(db.String)
    language: str = db.Column(db.String)
    proper: str = db.Column(db.String)
    quality: str = db.Column(db.String)
    region: str = db.Column(db.String)
    repack: str = db.Column(db.String)
    resolution: str = db.Column(db.String)
    season: str = db.Column(db.String)
    title: str = db.Column(db.String)
    website: str = db.Column(db.String)
    widescreen: str = db.Column(db.String)
    year: str = db.Column(db.String)
    job_id: str = db.Column(db.String)
    ignored: bool = db.Column(db.Boolean, nullable=False, default=False)

    created_datetime: datetime = db.Column(db.DateTime, default=datetime.utcnow)

    unmatched = db.relationship(UnmatchedItem, backref='parsed_media_item',
                                                         cascade="all", lazy=True, uselist=False)


    # reference to matched movie, if this media is already matched to a movie
    matched_movie_id: int = db.Column(db.Integer, db.ForeignKey('movie.id'),
                                      nullable=True)

    def __hash__(self):
        return id(self)

    def transient_copy(self):
        return ParsedMediaItem(
            filename=self.filename,
            target_filename=self.target_filename,
            path=self.path,
            target_path=self.target_path,
            audio=self.audio,
            codec=self.codec,
            container=self.container,
            episode=self.episode,
            episodeName=self.episodeName,
            garbage=self.garbage,
            group=self.group,
            hardcoded=self.hardcoded,
            language=self.language,
            proper=self.proper,
            quality=self.quality,
            region=self.region,
            repack=self.repack,
            resolution=self.resolution,
            season=self.season,
            title=self.title,
            website=self.website,
            widescreen=self.widescreen,
            year=self.year,
            job_id=self.job_id,
            ignored=self.ignored)

    def already_matched(self):
        return ParsedMediaItem.query.filter(and_(
            ParsedMediaItem.filename == self.filename,
            ParsedMediaItem.path == self.path,
            ParsedMediaItem.matched_movie_id.isnot(None)
        )).one_or_none()

    def already_linked(self):
        return self.target_path is not None

    def absolute_path(self):
        if not self.path or not self.filename:
            return None
        return os.path.join(self.path, self.filename)

    def absolute_target_path(self):
        if not self.target_path or not self.target_filename:
            return None
        return os.path.join(self.target_path, self.target_filename)

    def is_movie(self):
        return self.episode is None and self.season is None

    def is_tv(self):
        return not self.is_movie()

    def is_season(self):
        return self.season is not None

    def is_episode(self):
        return self.episode is not None

    def set_target_absolute_path(self, target_name):
        """
        Sets a target_filename and target_path from a formatted name. An assumption is that this is complete path
        to the movie which will be linked to this media item.

        :param target_name: a target path
        """
        self.target_filename = os.path.basename(target_name)
        self.target_path = os.path.dirname(target_name)

    @classmethod
    def schema(cls) -> Schema:
        return ParsedMediaItemSchema()
