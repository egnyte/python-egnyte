from egnyte import configuration, client
import unittest

CONFIG_NAME = 'test_config.json'
GROUP_NAME = "Python SDK test group"
NEW_GROUP_NAME = "New name"


class TestGroups(unittest.TestCase):
    def setUp(self):
        self.config = configuration.load(CONFIG_NAME)
        self.egnyte = client.EgnyteClient(self.config)
        self.user = self.egnyte.users.by_username(self.config['login'])
        self.groups = self.egnyte.groups
        self.group = self.__createGroup(self.groups, GROUP_NAME, [self.user])

    def tearDown(self):
        self.group.delete()

    def test_list_groups(self):
        all_groups = self.egnyte.groups.list()

        self.assertGreaterEqual(len(all_groups), 1)
        self.assertIn(self.group, all_groups)

    def test_create_group(self):
        created_group = self.groups.by_displayName(GROUP_NAME)

        self.assertEqual(created_group, self.group)
        self.assertEqual(created_group.members[0]['username'], self.config['login'])

    def test_update_group(self):
        self.group.full_update(NEW_GROUP_NAME)

        updated_group = self.groups.by_displayName(NEW_GROUP_NAME)
        self.assertEqual(updated_group.members[0]['username'], self.config['login'])

    def __createGroup(self, groups, name,  members=None):
        return groups.create(name, members)
