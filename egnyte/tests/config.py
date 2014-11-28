def createTestCase(config_file):
    import unittest
    import hashlib
    from egnyte import configuration, client

    config = configuration.load(config_file)
    root_folder_name = '/Shared/integration_test_python/%s' % hashlib.sha256(config.get('access_token', '').encode('ASCII')).hexdigest()

    class IntegrationCase(unittest.TestCase):
        def setUp(self):
            self.client = client.EgnyteClient(self.config)
            self.root_folder = self.client.folder(self.root_folder_name)

        def tearDown(self):
            self.client.close()
            del self.client

    IntegrationCase.config = config
    IntegrationCase.root_folder_name = root_folder_name

    return unittest.skipUnless(config.get('access_token') and config.get('domain'),
                               "No configuration for integration tests (%s), check doc/TESTS.md" % config_file)(IntegrationCase)


IntegrationCase = createTestCase('test_config.json')  # default test configuration
