import unittest

from egnyte import configuration

_config = configuration.load('test_config.json')

@unittest.skipUnless(_config.get('access_token') and _config.get('domain'),
                     "No configuration for integration tests, check doc/TESTS.md")
class TestCase(unittest.TestCase):
    config = _config