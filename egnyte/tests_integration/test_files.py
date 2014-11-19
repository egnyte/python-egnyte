from six import BytesIO

from egnyte import exc

from egnyte.tests_integration.config import TestCase


class TestFiles(TestCase):
    def setUp(self):
        super(TestFiles, self).setUp()
        self.filepath = self.root_folder.path + '/test.txt'
        self.root_folder.create()

    def test_create_file_bytesio(self):
        source = BytesIO(b'vijayendra')
        source.seek(0)

        self.client.create_folder(self.root_folder.path)
        self.client.put_file_contents(self.filepath, source)

        dest = BytesIO()
        self.client.get_file_contents(self.filepath).write_to(dest)

        dest.seek(0)
        source.seek(0)

        self.assertEqual(source.read(), dest.read(), "Uploaded and downloaded file's contents do not match")

    def test_create_file_strings(self):
        source = b'vijayendra'
        self.client.create_folder(self.root_folder.path)
        self.client.put_file_contents(self.filepath, source)

        dest = self.client.get_file_contents(self.filepath).read()

        self.assertEqual(source, dest, "Uploaded and downloaded file's contents do not match")

    def test_create_file_chunked(self):
        source = BytesIO(b'0123456789'*1024*10) # 100k bytes
        source.seek(0)
        self.client.upload_chunk_size = 40000
        self.client.create_folder(self.root_folder.path)
        self.client.put_file_contents(self.filepath, source)

        dest = BytesIO()
        self.client.get_file_contents(self.filepath).write_to(dest)

        dest.seek(0)
        source.seek(0)

        self.assertEqual(source.read(), dest.read(), "Uploaded and downloaded file's contents do not match")
