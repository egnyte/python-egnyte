import unittest

from egnyte import configuration, client

_config = configuration.load('test_config.json')

@unittest.skipUnless(_config.get('access_token') and _config.get('domain'),
                     "No configuration for integration tests, check doc/TESTS.md")
class TestCase(unittest.TestCase):
    config = _config

    def setUp(self):
        self.client = client.EgnyteClient(self.config)
        self.root_folder = self.client.folder('/Shared/integration_test_python')

    def tearDown(self):
        self.client.close()
        del self.client
