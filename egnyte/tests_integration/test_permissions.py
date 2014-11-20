from egnyte import exc

from egnyte.tests_integration.config import TestCase

class TestPermissions(TestCase):
    def test_permissions(self):
        folder = self.root_folder.folder("permissions_1").create()
        #print folder.get_permissions()
        #print folder.get_effective_permissions(self.config['login'])

