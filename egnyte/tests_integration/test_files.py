try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from config import TestCase
from egnyte import client

class TestFile(TestCase):
    def setUp(self):
        super(TestFile, self).setUp()
        self.folderpath = r'/Shared/integration_test_python'
        self.filepath = self.folderpath + '/test.txt'
        try:
            self.client.delete(self.folderpath)
        except client.NotFound:
            pass


    def tearDown(self):
        self.client.delete(self.folderpath)

    def test_create_file(self):
        source = StringIO('vijayendra')
        source.seek(0)

        self.client.create_folder(self.folderpath)
        self.client.put_file(self.filepath, source)

        dest = StringIO()
        for chunk in self.client.get_file(self.filepath):
            dest.write(chunk)

        dest.seek(0)
        source.seek(0)

        self.assertEqual(source.read(), dest.read(), "Uploaded and downloaded file's contents do not match")
