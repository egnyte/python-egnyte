from egnyte.tests.config import IntegrationCase

class TestSearch(IntegrationCase):
    def setUp(self):
        super(TestSearch, self).setUp()
        self.root_folder.create()
        self.filepath = self.root_folder.path + '/search/test1.txt'

    def test_file_search(self):
        source = b'Lorem ipsum'
        f = self.client.file(self.filepath)
        f.upload(source)
        d = self.client.search.files(u'ipsum')
        self.assertIsNotNone(d) # empty list is possible, as we won't get an answer here during the first run - it takes ~1min for file to pass through indexing pipeline
        if d:
            self.assert_(u'ipsum' in d[0].snippet)
            f = d[0].file()
