"""
Test settings API
"""

from __future__ import print_function

from unittest.case import skip

from egnyte.tests.config import IntegrationCase

class TestSettings(IntegrationCase):
    #@skip('Settings API not yet deployed.')
    def test_settings(self):
        print(self.client.settings)
