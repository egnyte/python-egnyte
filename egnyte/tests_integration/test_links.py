from egnyte import const

import unittest


from egnyte.tests_integration.config import TestCase


class TestLinks(TestCase):
    def setUp(self):
        super(TestLinks, self).setUp()
        self.folder = self.root_folder.folder('links_1')

    @unittest.skip("Links API treats IDs in a weird way - needs fixing")
    def test_folder_link_1(self):
        folder = self.client.folder(self.folder.path).create()
        data = folder.link(const.LINK_ACCESSIBILITY_ANYONE)
        url = data['links'][0]['url']
        #link = self.client.link_details(data['links'][0]['id'])
        #self.assertEqual(link['url'], url)
        #self.client.link_delete(data['links'][0]['id'])
