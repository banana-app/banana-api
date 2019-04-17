from dataclasses import dataclass
from marshmallow import Schema, fields
from banana.core import JsonMixin


class JobEventSchema(Schema):
    job_id = fields.String(required=True)
    job_type = fields.String(missing=None)
    event_type = fields.String(required=True)
    current_item = fields.Integer(missing=None)
    total_items = fields.Integer(missing=None)
    context = fields.String(missing=None)


class EventTypes:

    PROGRESS = 'progress'
    COMPLETED = 'completed'
    ERROR = 'error'


@dataclass
class JobProgressEvent(JsonMixin):

    job_id: str
    job_type: str
    event_type: str = EventTypes.PROGRESS
    current_item: int = None
    total_items: int = None
    context: str = None

    @classmethod
    def schema(cls) -> Schema:
        return JobEventSchema()


@dataclass
class JobErrorEvent(JsonMixin):

    job_id: str
    job_type: str
    event_type: str = EventTypes.ERROR
    current_item: int = None
    total_items: int = None
    context: str = None

    @classmethod
    def schema(cls) -> Schema:
        return JobEventSchema()


@dataclass
class JobCompletedEvent(JsonMixin):

    job_id: str
    job_type: str
    event_type: str = EventTypes.COMPLETED
    current_item: int = None
    total_items: int = None
    context: str = None

    @classmethod
    def schema(cls) -> Schema:
        return JobEventSchema()
