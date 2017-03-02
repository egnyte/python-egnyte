from egnyte.tests.config import EgnyteTestCase
from egnyte import exc
from helpers import upload_file

FILE_FIRST_VERSION_NAME = 'FILE1.png'
FILE_SECOND_VERSION_NAME = 'FILE2.png'
TEXT_FILE_CONTENT = 'test_content'
DOWNLOADED_FILE_NAME = 'DOWNLOADED.png'
EGNYTE_FILE_NAME_IMAGE = '/sample.png'
EGNYTE_FILE_NAME_TEXT = '/test.txt'
DESTINATION_FOLDER_NAME = 'to_here'


class TestFiles(EgnyteTestCase):
    def setUp(self):
        super(TestFiles, self).setUp()
        self.filepath = self.root_folder.path + EGNYTE_FILE_NAME_IMAGE
        self.root_folder.create()

    def test_upload_file(self):
        uploaded_file = upload_file(self.egnyte, FILE_FIRST_VERSION_NAME, self.filepath)

        self.assertIsNone(uploaded_file.check())

    def test_download_file(self):
        uploaded_file = self.egnyte.file(self.root_folder.path + EGNYTE_FILE_NAME_TEXT)
        uploaded_file.upload(TEXT_FILE_CONTENT)

        downloaded_file = uploaded_file.download()

        self.assertEqual(downloaded_file.response.status_code, 200)
        self.assertEqual(downloaded_file.read(), TEXT_FILE_CONTENT)

    def test_copy_file(self):
        destination = self.root_folder.folder(DESTINATION_FOLDER_NAME)
        destination.create()
        uploaded_file = upload_file(self.egnyte, FILE_FIRST_VERSION_NAME, self.filepath)

        copied_file = uploaded_file.copy(destination.path + EGNYTE_FILE_NAME_IMAGE)

        self.assertIsNone(uploaded_file.check())
        self.assertIsNone(copied_file.check())

    def test_move_file(self):
        destination = self.root_folder.folder(DESTINATION_FOLDER_NAME)
        destination.create()
        uploaded_file = upload_file(self.egnyte, FILE_FIRST_VERSION_NAME, self.filepath)

        moved_file = uploaded_file.move(destination.path + EGNYTE_FILE_NAME_IMAGE)

        with self.assertRaises(exc.NotFound):
            uploaded_file.check()
        self.assertIsNone(moved_file.check())

    def test_delete_file(self):
        uploaded_file = upload_file(self.egnyte, FILE_FIRST_VERSION_NAME, self.filepath)

        self.assertIsNone(uploaded_file.check())

        uploaded_file.delete()

        with self.assertRaises(exc.NotFound):
            uploaded_file.check()

    def test_upload_new_version(self):
        upload_file(self.egnyte, FILE_FIRST_VERSION_NAME, self.filepath)
        second_version = upload_file(self.egnyte, FILE_SECOND_VERSION_NAME, self.filepath)
        file_attributes = second_version._fetch_attributes()

        self.assertEqual(file_attributes['num_versions'], 2)
