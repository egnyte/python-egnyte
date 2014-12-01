from __future__ import print_function

from egnyte.tests.config import IntegrationCase

class TestPermissions(IntegrationCase):
    def test_permissions(self):
        folder = self.root_folder.folder("permissions_1").create(True)
        permissions = folder.get_permissions()
        self.assertEquals(permissions.user_to_permission[self.config['login']], 'Owner')
        self.assertIn(self.config['login'], permissions.permission_to_owner['Owner']['users'])

    def test_effective(self):
        self.client.folder("/Shared").get_effective_permissions(self.config['login'])
        folder = self.root_folder.folder("permissions_1").create(True)
        effective = folder.get_effective_permissions(self.config['login'])
        self.assertEquals('Owner', effective)
