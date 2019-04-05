import unittest
from banana.events import *
import uuid
import json


class EventTests(unittest.TestCase):

    def test_progress_event(self):
        event1_id = uuid.uuid4()
        event1 = JobProgressEvent(job_id=str(event1_id), job_type="scan")
        event2 = JobProgressEvent(job_id=str(event1_id), job_type="scan", current_item=100, total_items=200)

        event1_dict = json.loads(event1.to_json())
        event2_dict = json.loads(event2.to_json())

        self.assertEqual(str(event1_id), event1_dict.get('job_id'))
        self.assertEqual('scan', event1_dict.get('job_type'))
        self.assertEqual(EventTypes.PROGRESS, event1_dict.get('event_type'))
        self.assertEqual(None, event1_dict.get('total_items'))
        self.assertEqual(None, event1_dict.get('processed_items'))

        self.assertEqual(str(event1_id), event2_dict.get('job_id'))
        self.assertEqual('scan', event2_dict.get('job_type'))
        self.assertEqual(EventTypes.PROGRESS, event2_dict.get('event_type'))
        self.assertEqual(200, event2_dict.get('total_items'))
        self.assertEqual(100, event2_dict.get('current_item'))

    def test_error_event(self):
        event1_id = uuid.uuid4()
        event1 = JobErrorEvent(job_id=str(event1_id), job_type="scan")

        event1_dict = json.loads(event1.to_json())

        self.assertEqual(str(event1_id), event1_dict.get('job_id'))
        self.assertEqual('scan', event1_dict.get('job_type'))
        self.assertEqual(EventTypes.ERROR, event1_dict.get('event_type'))
        self.assertEqual(None, event1_dict.get('total_items'))
        self.assertEqual(None, event1_dict.get('processed_items'))

    def test_completed_event(self):
        event1_id = uuid.uuid4()
        event1 = JobCompletedEvent(job_id=str(event1_id), job_type="scan")

        event1_dict = json.loads(event1.to_json())

        self.assertEqual(str(event1_id), event1_dict.get('job_id'))
        self.assertEqual('scan', event1_dict.get('job_type'))
        self.assertEqual(EventTypes.COMPLETED, event1_dict.get('event_type'))
        self.assertEqual(None, event1_dict.get('total_items'))
        self.assertEqual(None, event1_dict.get('processed_items'))
