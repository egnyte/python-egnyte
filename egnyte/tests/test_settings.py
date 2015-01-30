"""
Test settings API
"""

from __future__ import print_function

from egnyte.tests.config import IntegrationCase

class TestSettings(IntegrationCase):
    def test_settings(self):
        settings = self.client.settings
        self.assertIn("audit", settings)
        self.assertIn("file_system", settings)
        self.assertIn("users", settings)
        self.assertIn("links", settings)



