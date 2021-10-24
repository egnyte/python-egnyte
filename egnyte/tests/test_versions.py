from six import BytesIO

from egnyte.tests.config import IntegrationCase

class TestVersions(IntegrationCase):
    def setUp(self):
        super(TestVersions, self).setUp()
        self.filepath = self.root_folder.path + '/test_versions.txt'
        self.root_folder.create()
        self.version_count = 3

    def test_file_versions(self):
        self.client.folder(self.root_folder.path).create()
        str_append = 'is cool '

        for index in range(self.version_count):
            str_append *= (index + 1)
            source = BytesIO(b'PythonEgnyte %s' % str_append)
            source.seek(0)
            self.client.file(self.filepath).upload(source)

        versions = self.client.file(self.filepath)
        self.assertEqual(
            len(versions), 
            self.version_count-1, 
            "Version count does not match")

        attr_list = [
            'checksum', 
            'last_modified', 
            'entry_id', 
            'is_folder', 
            'uploaded_by', 
            'size']

        for attr in attr_list:
            self.assertIn(
                attr, 
                versions.keys(), 
                'attribute %s not found in versions' % attr
                )
