import md5
import unittest

from egnyte import client
from egnyte import const
from egnyte.tests import const as tests_const

class TestRequestsAuth(unittest.TestCase):
    def test_oauth_str(self):
        auth = client.RequestsAuth('abc')
        self.assertEqual(auth._oauth_str(), "Bearer abc")
        
    def test_auth(self):
        auth = client.RequestsAuth('abc')

class BaseEgnyte(unittest.TestCase):
    def setUp(self):
        auth = client.RequestsAuth(tests_const.ACCESS_TOKEN)
        self.egnyte_obj = client.EgnyteClient(tests_const.DOMAIN, auth)
        self.folderpath = r'/Shared/test'
        self.filepath = self.folderpath + '/test.txt'
        self.destination = r'/Shared/abc'
        self.egnyte_obj.delete(self.folderpath)
        self.egnyte_obj.delete(self.destination)

class TestEgnyteClient(BaseEgnyte):
    def test_init(self):
        self.assertEqual(self.egnyte_obj.domain, tests_const.DOMAIN)
        self.assertEqual(type(self.egnyte_obj.auth), client.RequestsAuth)

    def test_get_url(self):
        base_url = self.egnyte_obj.get_url("")
        self.assertEqual(base_url, "https://%s.%s" % (tests_const.DOMAIN, tests_const.SERVER))

    def test_encode_path(self):
        path = self.egnyte_obj.encode_path(" ")
        self.assertEqual(path, r"%20")

    def test_userinfo(self):
        r = self.egnyte_obj.userinfo()
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data), 3)
        self.assertEqual(data["username"], tests_const.USERNAME)

class TestFolder(BaseEgnyte):
    def test_folder(self):
        r = self.egnyte_obj.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201) # success
        r = self.egnyte_obj.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 403) # already exists
        r = self.egnyte_obj.delete(self.folderpath)
        self.assertEqual(r.status_code, 200) # deleted
        r = self.egnyte_obj.delete(self.folderpath)
        self.assertEqual(r.status_code, 404) # folder not found
        
    def test_folder_move(self):
        r = self.egnyte_obj.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201) # success
        r = self.egnyte_obj.move(self.folderpath, self.destination)
        self.assertEqual(r.status_code, 200) 
        r = self.egnyte_obj.delete(self.folderpath)
        self.assertEqual(r.status_code, 404) 
        r = self.egnyte_obj.delete(self.destination)
        self.assertEqual(r.status_code, 200) 
        
    def test_folder_copy(self):
        r = self.egnyte_obj.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201) # success
        r = self.egnyte_obj.copy(self.folderpath, self.destination)
        self.assertEqual(r.status_code, 200) 
        r = self.egnyte_obj.delete(self.folderpath)
        self.assertEqual(r.status_code, 200) 
        r = self.egnyte_obj.delete(self.destination)
        self.assertEqual(r.status_code, 200) 
        
    def test_folder_list(self):
        r = self.egnyte_obj.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201) # success
        r = self.egnyte_obj.list_content(self.folderpath)
        self.assertEqual(r.status_code, 200) 
        data = r.json()
        self.assertEqual(data['is_folder'], True)
        self.assertEqual(data['name'], 'test')
        self.assert_('folders' not in data)
        r = self.egnyte_obj.delete(self.folderpath)
        self.assertEqual(r.status_code, 200)

    def test_folder_create_link(self):
        r = self.egnyte_obj.create_folder(self.folderpath)
        self.assertEqual(r.status_code, 201) # success
        r = self.egnyte_obj.create_link(
            self.folderpath,
            const.LINK_KIND_FOLDER,
            const.LINK_ACCESSIBILITY_ANYONE,
            )
        self.assertEqual(r.status_code, 200) # success
        data = r.json()
        url = data['links'][0]['url']
        r = self.egnyte_obj.link_details(data['links'][0]['id'])
        self.assertEqual(r.status_code, 200) # success
        self.assertEqual(r.json()['url'], url)
        r = self.egnyte_obj.delete_link(data['links'][0]['id'])
        self.assertEqual(r.status_code, 200) # success
        
class TestFile(BaseEgnyte):
    def test_create_file(self):
        data = 'vijayendra'
        with open('/tmp/test.txt', 'wb') as fptr:
            fptr.write(data)
            
        with open('/tmp/test.txt', 'rb') as fptr:
            r = self.egnyte_obj.create_folder(self.folderpath)
            self.assertEqual(r.status_code, 201) # success
            r = self.egnyte_obj.put_file(self.filepath, fptr)
            self.assertEqual(r.status_code, 200) # success  ##########XXXXXXXXXXX Wrong in Doc

        with open('/tmp/test1.txt', 'wb') as fptr:
            r = self.egnyte_obj.get_file(self.filepath, fptr)
            self.assertEqual(r.status_code, 200) # success

        with open('/tmp/test1.txt', 'rb') as fptr:
            self.assertEqual(fptr.read(), data)
            
