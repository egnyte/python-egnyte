from __future__ import print_function

from egnyte.tests.config import IntegrationCase


class TestUserInfo(IntegrationCase):
    def test_userinfo(self):
        data = self.client.user_info
        self.assertEqual(data["username"], self.config['login'], "Username received from API does not match one in config file")


class TestUsers(IntegrationCase):
    def test_create_and_search(self):
        users = self.client.users
        user = users.create(userName="test_user_1", externalId="test_user_1", email="test_user_1@example.com",
                            familyName="John", givenName="Doe", active=False, sendInvite=False)
        try:
            search = users.list()
            self.assertIn(user, search, "User should be in list of all users")

            user2 = users.by_email("test_user_1@example.com")
            self.assertEqual(user, user2, "Should find user by email")
            user3 = users.by_username("test_user_1")
            self.assertEqual(user, user3, "Should find user by username")

            user.update(email="another_email@example.com")
            user4 = users.by_email("test_user_1@example.com")
            self.assertIsNone(user4, "Should not find user after email has changed")

        finally:
            user.delete()

class TestGroups(IntegrationCase):
    groupName = "python integration test group"

    def test_create(self):
        user = self.client.users.by_username(self.config['login'])
        groups = self.client.groups

        group1 = groups.create(self.groupName, [user])
        try:
            group2 = groups.by_displayName(self.groupName)
            self.assertEqual(group1, group1)
            self.assertEqual(group2.members[0]['username'], self.config['login'])
        finally:
            group1.delete()