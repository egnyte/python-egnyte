from egnyte import exc

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
        folder = self.client.folder(self.folder.path).create()
        subfolder = folder.folder("test1").create()
        file = folder.file("test2")
        file.upload(b"test111")
        data = folder.list()
        folders = list(data['folders'])
        files = list(data['files'])
        self.assertEqual(1, len(folders), "There should be one subfolder")
        self.assertEqual(folders[0]._url, subfolder._url, "Subfolder URLs should be identical")
        self.assertEqual(1, len(files), "There should be one filer")
        self.assertEqual(files[0]._url, file._url, "File URLs should be identical")
        folder.delete()
