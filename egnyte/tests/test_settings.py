"""
Test settings API
"""

import unittest
from egnyte import configuration, client

CONFIG_NAME = 'test_config.json'

class TestSettings(unittest.TestCase):
    settings = None

    def setUp(self):
        self.config = configuration.load(CONFIG_NAME)
        self.egnyte = client.EgnyteClient(self.config)

    def test_audit_settings(self):
        audit = self.__fetch_settings()["audit"]

        self.assertIn("archive_audit_reports", audit)

    def test_file_system_settings(self):
        file_system = self.__fetch_settings()["file_system"]

        self.assertIn("locale", file_system)
        self.assertIn("total", file_system)
        self.assertIn("used", file_system)

    def test_users_settings(self):
        users = self.__fetch_settings()["users"]

        self.assertIn("licenses", users)
        self.assertIn("sso_enabled", users)
        self.assertIn("power_user_rights", users)

    def test_links_settings(self):
        links = self.__fetch_settings()["links"]

        self.assertIn("folder_links", links)
        self.assertIn("file_links", links)
        self.assertIn("expiration", links)

    def __fetch_settings(self):
        if TestSettings.settings is None:
            TestSettings.settings = self.egnyte.settings
        return TestSettings.settings
