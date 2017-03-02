from egnyte import configuration, client, exc
import unittest

CONFIG_NAME = 'test_config.json'
ROOT_FOLDER_PATH = '/Shared/test_python_sdk/'


class EgnyteTestCase(unittest.TestCase):
    def setUp(self):
        self.config = configuration.load(CONFIG_NAME)
        self.egnyte = client.EgnyteClient(self.config)

        self.root_folder = self.egnyte.folder(ROOT_FOLDER_PATH)

    def tearDown(self):
        self.egnyte.folder(ROOT_FOLDER_PATH).delete()
        self.egnyte.close()
        del self.egnyte
