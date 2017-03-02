from egnyte.tests.config import EgnyteTestCase

TEST_FOLDER_NAME = 'permissions'
USER_NAME = 'test_permissions_user'
GROUP_NAME = 'test_permissions_group'


class TestDeprecatedPermissions(EgnyteTestCase):
    def setUp(self):
        super(TestDeprecatedPermissions, self).setUp()
        self.folder = self.root_folder.folder(TEST_FOLDER_NAME)
        self.user = self.egnyte.users.create(userName=USER_NAME,
                                             externalId=USER_NAME,
                                             email='test@example.com',
                                             familyName='Doe',
                                             givenName='John',
                                             active=False,
                                             sendInvite=False)
        self.group = self.egnyte.groups.create(GROUP_NAME, members=[self.user])

    def tearDown(self):
        self.user.delete()
        self.group.delete()
        super(TestDeprecatedPermissions, self).tearDown()

    def test_permissions_for_folder_creator(self):
        self.folder.create(True)
        permissions = self.folder.get_permissions()

        self.assertEquals(permissions.user_to_permission[self.config['login']], 'Owner')
        self.assertIn(self.config['login'], permissions.permission_to_owner['Owner']['users'])

    def test_effective_permissions(self):
        self.folder.create(True)

        effective = self.folder.get_effective_permissions(self.config['login'])
        self.assertEquals('Owner', effective)

    def test_set_user_permissions(self):
        self.folder.create(True)

        self.folder.set_permissions('Editor', users=[USER_NAME])
        permissions = self.folder.get_permissions()

        self.assertEquals(permissions.user_to_permission[USER_NAME], 'Editor')

    def test_set_group_permissions(self):
        self.folder.create(True)

        self.folder.set_permissions('Viewer', groups=[GROUP_NAME])
        permissions = self.folder.get_permissions()

        self.assertEquals(permissions.group_to_permission[GROUP_NAME], 'Viewer')
