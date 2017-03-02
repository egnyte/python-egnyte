from egnyte.tests.config import EgnyteTestCase

FOLDER_NAME = 'EVENT'


class TestEvents(EgnyteTestCase):
    def setUp(self):
        super(TestEvents, self).setUp()
        self.root_folder.create()

    def test_filter_poll(self):
        events = self.egnyte.events
        events = events.filter(events.oldest_event_id)
        results = events.poll(count=1)
        self.assertNotEqual(0, len(results), "Poll results should not be empty")
        self.assertNotEqual(events.start_id, events.oldest_event_id,
                            "latest_event_id should have been bumped after non-empty poll")

    def test_register_new_events(self):
        folder = self.root_folder.folder(FOLDER_NAME).create()

        events = self.egnyte.events
        events = events.filter(events.latest_event_id - 1)
        results = events.poll(count=1)

        self.assertEqual(results[0].action_source, 'PublicAPI')
        self.assertEqual(results[0].action, 'create')
        self.assertEqual(results[0].data['target_path'], folder.path)
        self.assertEqual(results[0].data['is_folder'], True)
