"""
Test settings API
"""

from __future__ import print_function

from unittest.case import expectedFailure

from egnyte.tests.config import IntegrationCase

class TestSettings(IntegrationCase):
    @expectedFailure
    def test_settings(self):
        settings = self.client.settings
        self.assertContains("general", settings)
        self.assertContains("audit", settings)
        self.assertContains("file_system", settings)
        self.assertContains("users", settings)
        self.assertContains("links", settings)

