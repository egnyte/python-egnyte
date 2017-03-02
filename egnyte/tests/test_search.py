from egnyte.tests.config import EgnyteTestCase

FILE_PATH = '/search/test1.txt'
FILE_CONTENT = b'Lorem ipsum'
SEARCH_QUERY = u'ipsum'


class TestSearch(EgnyteTestCase):
    def setUp(self):
        super(TestSearch, self).setUp()
        self.root_folder.create()
        self.filepath = self.root_folder.path + FILE_PATH

    def test_file_search(self):
        _file = self.egnyte.file(self.filepath)
        _file.upload(FILE_CONTENT)
        search_results = self.egnyte.search.files(SEARCH_QUERY)
        # empty list is possible, as we won't get an answer here during the first run:
        # it takes ~1min for file to pass through indexing pipeline
        self.assertIsNotNone(search_results)
        if search_results:
            self.assert_(SEARCH_QUERY in search_results[0].snippet)
