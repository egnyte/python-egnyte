try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from config import TestCase
from egnyte import exc

class TestFiles(TestCase):
    def setUp(self):
        super(TestFiles, self).setUp()
        self.folderpath = r'/Shared/integration_test_python'
        self.filepath = self.folderpath + '/test.txt'

    def tearDown(self):
        try:
            self.client.delete_folder(self.folderpath)
        except exc.NotFound:
            pass

    def test_create_file(self):
        source = StringIO('vijayendra')
        source.seek(0)

        self.client.create_folder(self.folderpath)
        self.client.put_file_contents(self.filepath, source)

        dest = StringIO()
        self.client.get_file_contents(self.filepath).write_to(dest)

        dest.seek(0)
        source.seek(0)

        self.assertEqual(source.read(), dest.read(), "Uploaded and downloaded file's contents do not match")
