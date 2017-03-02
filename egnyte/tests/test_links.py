from egnyte import exc
from egnyte.tests.config import EgnyteTestCase
from helpers import upload_file
import datetime

RECIPIENT_EMAIL_1 = 'test1@example.com'
RECIPIENT_EMAIL_2 = 'test2@example.com'
EGNYTE_FILE_NAME = '/sample.png'
FILE_NAME = 'FILE1.png'
ACCESSIBILITY_ANYONE = 'anyone'
ACCESSIBILITY_DOMAIN = 'domain'


class TestLinks(EgnyteTestCase):
    def setUp(self):
        super(TestLinks, self).setUp()
        self.filepath = self.root_folder.path + EGNYTE_FILE_NAME
        self.folder = self.root_folder.create()

    def test_create_file_link(self):
        uploaded_file = upload_file(self.egnyte, FILE_NAME, self.filepath)
        link = uploaded_file.link(ACCESSIBILITY_ANYONE)

        self.__verify_link(link[0], self.filepath, ACCESSIBILITY_ANYONE, 'file')

    def test_create_folder_link(self):
        link = self.folder.link(ACCESSIBILITY_DOMAIN)

        self.__verify_link(link[0], self.root_folder.path, ACCESSIBILITY_DOMAIN, 'folder')

    def test_delete_link(self):
        link = self.folder.link(ACCESSIBILITY_DOMAIN)

        self.__verify_link(link[0], self.root_folder.path, ACCESSIBILITY_DOMAIN, 'folder')

        link[0].delete()

        with self.assertRaises(exc.NotFound):
            link[0].check()

    def test_several_links(self):
        links = self.folder.link(ACCESSIBILITY_ANYONE,
                                 recipients=[RECIPIENT_EMAIL_1, RECIPIENT_EMAIL_2],
                                 send_email=False)

        self.assertEqual(links[0].path, links[1].path, "Both links should point to the same file")
        self.assertEqual((RECIPIENT_EMAIL_1,), tuple(links[0].recipients), "Link one should be for first email")
        self.assertNotEqual(links[0].id, links[1].id, "Links should have different ids")

        links[0].delete()

        self.assertIsNone(links[1].check())  # link two should still exist
        self.assertRaises(exc.NotFound, links[0].check)  # link one should no longer exist

    def test_list_links(self):
        links = self.egnyte.links
        all_links = links.list()
        tomorrow = datetime.datetime.now() + datetime.timedelta(1)
        future = links.list(created_after=tomorrow)

        self.assertEqual([], future, "List of links created after tomorrow should be empty")
        self.assertEqual(0, future.total_count, "Total count of links created after tomorrow should be 0")

        past = links.list(created_before=tomorrow)

        self.assertEqual(tuple(all_links), tuple(past),
                         "List of links created before tomorrow should include all links")

    def __verify_link(self, link, path, accessibility, link_type):
        self.assertEqual(link.path, path)
        self.assertEqual(link.accessibility, accessibility)
        self.assertEqual(link.type, link_type)
