from egnyte.tests.config import EgnyteTestCase
from egnyte.tests.helpers import upload_file

EGNYTE_FILE_NAME = '/sample.png'
FILE_NAME = 'FILE1.png'
COMMENT = 'test comment'


class TestComments(EgnyteTestCase):
    def setUp(self):
        super(TestComments, self).setUp()
        self.filepath = self.root_folder.path + EGNYTE_FILE_NAME
        self.root_folder.create()

    def test_create_file_comment(self):
        uploaded_file = upload_file(self.egnyte, FILE_NAME, self.filepath)
        comment = uploaded_file.add_note(COMMENT)

        self.assertEqual(comment.file_path, self.filepath)
        self.assertEqual(comment.message, COMMENT)

    def test_delete_file_comment(self):
        uploaded_file = upload_file(self.egnyte, FILE_NAME, self.filepath)
        comment = uploaded_file.add_note(COMMENT)

        all_comments = self.egnyte.notes.list()

        self.assertIn(comment, all_comments)

        comment.delete()
        all_comments = self.egnyte.notes.list()

        self.assertNotIn(comment, all_comments)

    def test_list_comments(self):
        uploaded_file = upload_file(self.egnyte, FILE_NAME, self.filepath)
        comment = uploaded_file.add_note(COMMENT)

        all_comments = self.egnyte.notes.list()

        self.assertIn(comment, all_comments)
        self.assertEqual(uploaded_file, comment.get_file())

        comments = uploaded_file.get_notes()

        self.assertEqual(tuple(comments), (comment,))

        comment.delete()
        comments = uploaded_file.get_notes()

        self.assertEqual(tuple(comments), ())

        all_comments = self.egnyte.notes.list()

        self.assertNotIn(comment, all_comments)
