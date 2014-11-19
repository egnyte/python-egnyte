from egnyte import exc
from egnyte.base import Const

from egnyte.tests_integration.config import TestCase


class TestFolders(TestCase):
    def setUp(self):
        super(TestFolders, self).setUp()
        self.folder = self.root_folder.folder('1')
        self.dest = self.root_folder.folder('2')
        self.file = self.folder.file('test.txt')

    def tearDown(self):
        try:
            self.folder.delete()
        except exc.NotFound:
            pass
        try:
            self.dest.delete()
        except exc.NotFound:
            pass
        super(TestFolders, self).tearDown()

    def test_folder(self):
        self.folder.create()
        with self.assertRaises(exc.InsufficientPermissions):
            self.folder.create(False)
        self.folder.delete()
        with self.assertRaises(exc.NotFound):
            self.folder.delete()

    def test_folder_move(self):
        self.folder.create()
        moved = self.folder.move(self.dest.path)
        self.assertEqual(moved.path, self.dest.path, "Moved folder path should be identical")
        with self.assertRaises(exc.NotFound):
            self.folder.delete()
        self.dest.delete()

    def test_folder_copy(self):
        self.folder.create()
        copied = self.folder.copy(self.dest.path)
        self.assertEqual(copied.path, self.dest.path, "Copied folder path should be identical")
        self.folder.delete()
        self.dest.delete()

    def test_folder_list(self):
        self.client.create_folder(self.folder.path)
        data = self.client.list_content(self.folder.path)
        self.assertEqual(data['is_folder'], True)
        self.assertTrue('folders' not in data)
        self.client.delete_folder(self.folder.path)

    def test_folder_link_create(self):
        self.client.create_folder(self.folder.path)
        data = self.client.link_create(
            self.folder.path,
            Const.LINK_KIND_FOLDER,
            Const.LINK_ACCESSIBILITY_ANYONE,
        )
        url = data['links'][0]['url']
        link = self.client.link_details(data['links'][0]['id'])
        self.assertEqual(link['url'], url)
        self.client.link_delete(data['links'][0]['id'])
