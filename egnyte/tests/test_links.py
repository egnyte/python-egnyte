from __future__ import print_function

import datetime

from egnyte import exc
from egnyte.tests.config import IntegrationCase


class TestLinks(IntegrationCase):
    def test_folder_link_duplicates(self):
        folder = self.root_folder.folder("link_duplicates").create()
        links = folder.link("anyone", recipients=['test1@example.com', 'test2@example.com'], send_email=False)
        link_one = links[0]
        link_two = links[1]
        self.assertEqual(link_one.path, link_two.path, "Both links should point to the same file")
        self.assertEqual(("test1@example.com",), tuple(link_one.recipients), "Link one should be for first email")
        self.assertNotEqual(link_one.id, link_two.id, "Links should have different ids")

        link_one.delete()
        link_two.check()  # link two should still exist
        self.assertRaises(exc.NotFound, link_one.check)  # link one should no longer exist
        link_two.delete()

    def test_links(self):
        links = self.client.links
        all = links.list()
        tomorrow = datetime.datetime.now() + datetime.timedelta(1)
        future = links.list(created_after=tomorrow)
        self.assertEqual([], future, "List of links created after tomorrow should be empty")
        self.assertEqual(0, future.total_count, "Total count of links created after tomorrow should be 0")
        past = links.list(created_before=tomorrow)
        self.assertEqual(tuple(all), tuple(past), "List of links created before tomorrow should include all links")
