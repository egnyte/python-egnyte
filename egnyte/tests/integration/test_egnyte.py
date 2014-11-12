from egnyte import client
from egnyte import const
from testconfig import TestCase


class BaseEgnyte(TestCase):
    def setUp(self):
        self.client = client.EgnyteClient(self.config)
        self.folderpath = r'/Shared/test'
        self.filepath = self.folderpath + '/test.txt'
        self.destination = r'/Shared/abc'
        self.client.delete(self.folderpath)
        self.client.delete(self.destination)


class TestEgnyteClient(BaseEgnyte):
    def test_userinfo(self):
        r = self.client.userinfo()
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data["username"], self.config['login'])


class TestFolder(BaseEgnyte):
    def test_folder(self):
        r = self.client.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201)  # success
        r = self.client.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 403)  # already exists
        r = self.client.delete(self.folderpath)
        self.assertEqual(r.status_code, 200)  # deleted
        r = self.client.delete(self.folderpath)
        self.assertEqual(r.status_code, 404)  # folder not found

    def test_folder_move(self):
        r = self.client.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201)  # success
        r = self.client.move(self.folderpath, self.destination)
        self.assertEqual(r.status_code, 200)
        r = self.client.delete(self.folderpath)
        self.assertEqual(r.status_code, 404)
        r = self.client.delete(self.destination)
        self.assertEqual(r.status_code, 200)

    def test_folder_copy(self):
        r = self.client.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201)  # success
        r = self.client.copy(self.folderpath, self.destination)
        self.assertEqual(r.status_code, 200)
        r = self.client.delete(self.folderpath)
        self.assertEqual(r.status_code, 200)
        r = self.client.delete(self.destination)
        self.assertEqual(r.status_code, 200)

    def test_folder_list(self):
        r = self.client.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201)  # success
        r = self.client.list_content(self.folderpath)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(data['is_folder'], True)
        self.assertEqual(data['name'], 'test')
        self.assert_('folders' not in data)
        r = self.client.delete(self.folderpath)
        self.assertEqual(r.status_code, 200)

    def test_folder_create_link(self):
        r = self.client.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201)  # success
        r = self.client.create_link(
            self.folderpath,
            const.LINK_KIND_FOLDER,
            const.LINK_ACCESSIBILITY_ANYONE,
        )
        self.assertEqual(r.status_code, 200)  # success
        data = r.json()
        url = data['links'][0]['url']
        r = self.client.link_details(data['links'][0]['id'])
        self.assertEqual(r.status_code, 200)  # success
        self.assertEqual(r.json()['url'], url)
        r = self.client.delete_link(data['links'][0]['id'])
        self.assertEqual(r.status_code, 200)  # success


class TestFile(BaseEgnyte):
    def test_create_file(self):
        data = 'vijayendra'
        with open('/tmp/test.txt', 'wb') as fptr:
            fptr.write(data)

        with open('/tmp/test.txt', 'rb') as fptr:
            r = self.client.create_folder(self.folderpath)
            self.assertEqual(r.status_code, 201)  # success
            r = self.client.put_file(self.filepath, fptr)
            self.assertEqual(r.status_code, 200)  # success  ##########XXXXXXXXXXX Wrong in Doc

        with open('/tmp/test1.txt', 'wb') as fptr:
            r = self.client.get_file(self.filepath, fptr)
            self.assertEqual(r.status_code, 200)  # success

        with open('/tmp/test1.txt', 'rb') as fptr:
            self.assertEqual(fptr.read(), data)
