from egnyte import client, exc
from config import TestCase


class TestFolder(TestCase):
    def setUp(self):
        super(TestFolder, self).setUp()
        self.folderpath = r'/Shared/integration_test_python'
        self.destination = r'/Shared/integration_test_python2'
        self.filepath = self.folderpath + '/test.txt'
        try:
            self.client.delete(self.folderpath)
        except exc.NotFound:
            pass
        try:
            self.client.delete(self.destination)
        except exc.NotFound:
            pass

    def tearDown(self):
        pass

    def test_folder(self):
        self.client.create_folder(self.folderpath)
        with self.assertRaises(exc.InsufficientPermissions):
            self.client.create_folder(self.folderpath)
        self.client.delete(self.folderpath)
        with self.assertRaises(exc.NotFound):
            self.client.delete(self.folderpath)

    def test_folder_move(self):
        self.client.create_folder(self.folderpath)
        self.client.move(self.folderpath, self.destination)
        with self.assertRaises(exc.NotFound):
            self.client.delete(self.folderpath)
        self.client.delete(self.destination)

    def test_folder_copy(self):
        self.client.create_folder(self.folderpath)
        self.client.copy(self.folderpath, self.destination)
        self.client.delete(self.folderpath)
        self.client.delete(self.destination)

    def test_folder_list(self):
        self.client.create_folder(self.folderpath)
        data = self.client.list_content(self.folderpath)
        self.assertEqual(data['is_folder'], True)
        self.assertEqual(data['name'], 'integration_test_python')
        self.assert_('folders' not in data)
        self.client.delete(self.folderpath)

    def test_folder_create_link(self):
        self.client.create_folder(self.folderpath)
        data = self.client.create_link(
            self.folderpath,
            client.Const.LINK_KIND_FOLDER,
            client.Const.LINK_ACCESSIBILITY_ANYONE,
        )
        url = data['links'][0]['url']
        link = self.client.link_details(data['links'][0]['id'])
        self.assertEqual(link['url'], url)
        self.client.link_delete(data['links'][0]['id'])


