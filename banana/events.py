from dataclasses import dataclass
from banana.common.json import json_serializable


class EventTypes(object):

    PROGRESS = 'progress'
    COMPLETED = 'completed'
    ERROR = 'error'


@dataclass
@json_serializable
class JobProgressEvent(object):

    job_id: str
    job_type: str
    event_type: str = EventTypes.PROGRESS
    current_item: int = None
    total_items: int = None
    context: str = None


@dataclass
@json_serializable
class JobErrorEvent(object):

    job_id: str
    job_type: str
    event_type: str = EventTypes.ERROR
    current_item: int = None
    total_items: int = None
    context: str = None


@dataclass
@json_serializable
class JobCompletedEvent(object):

    job_id: str
    job_type: str
    event_type: str = EventTypes.COMPLETED
    current_item: int = None
    total_items: int = None
    context: str = None


