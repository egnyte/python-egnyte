from six import BytesIO

from egnyte.tests.config import IntegrationCase


class TestFiles(IntegrationCase):
    def setUp(self):
        super(TestFiles, self).setUp()
        self.filepath = self.root_folder.path + '/test.txt'
        self.root_folder.create()

    def test_create_file_bytesio(self):
        source = BytesIO(b'vijayendra')
        source.seek(0)

        self.client.folder(self.root_folder.path).create()
        self.client.file(self.filepath).upload(source)

        dest = BytesIO()
        self.client.file(self.filepath).download().write_to(dest)

        dest.seek(0)
        source.seek(0)

        self.assertEqual(source.read(), dest.read(), "Uploaded and downloaded file's contents do not match")

    def test_create_file_strings(self):
        source = b'vijayendra'
        self.client.folder(self.root_folder.path).create()
        self.client.file(self.filepath).upload(source)

        dest = self.client.file(self.filepath).download().read()

        self.assertEqual(source, dest, "Uploaded and downloaded file's contents do not match")

    def test_create_file_chunked(self):
        source = BytesIO(b'0123456789' * 1024 * 10)  # 100k bytes
        source.seek(0)
        self.client.folder(self.root_folder.path).create()

        f = self.client.file(self.filepath)
        f.upload_chunk_size = 40000
        f.upload(source)

        dest = BytesIO()
        self.client.file(self.filepath).download().write_to(dest)

        dest.seek(0)
        source.seek(0)

        self.assertEqual(source.read(), dest.read(), "Uploaded and downloaded file's contents do not match")

        partial_start = 5009
        partial_size = 104
        partial = f.download((partial_start, partial_start + partial_size - 1))
        source.seek(partial_start)

        source_content = source.read(partial_size)
        partial_content = partial.read()
        self.assertEqual(source_content, partial_content, "Partial download content does not match")
