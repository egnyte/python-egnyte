from config import TestCase

class TestUserInfo(TestCase):
    def test_userinfo(self):
        data = self.client.userinfo()
        self.assertEqual(data["username"], self.config['login'], "Username received from API does not match one in config file")
