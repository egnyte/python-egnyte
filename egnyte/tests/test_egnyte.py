import unittest

from egnyte import client
from egnyte import const


class TestRequestsAuth(unittest.TestCase):
    def test_oauth_str(self):
        auth = client.RequestsAuth('abc')
        self.assertEqual(auth._oauth_str(), "Bearer abc")

    def test_auth(self):
        client.RequestsAuth('abc')


