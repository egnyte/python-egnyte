from egnyte.tests.config import IntegrationCase

class TestEvents(IntegrationCase):
    def setUp(self):
        super(TestEvents, self).setUp()
        self.root_folder.create()
        self.filepath = self.root_folder.path + '/search/test1.txt'

    def test_filter_poll(self):
        events = self.client.events
        events = events.filter(events.oldest_event_id)
        results =  events.poll(count=1)
        self.assertNotEqual(0, len(results), "Poll results should not be empty")
        self.assertNotEqual(events.start_id, events.oldest_event_id, "latest_event_id should have been bumped after non-empty poll")
