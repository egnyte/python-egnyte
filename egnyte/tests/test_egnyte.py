import unittest

from egnyte import client


class TestRequestsAuth(unittest.TestCase):
    def test_oauth(self):
        auth = client.oauth('abc')
        class FakeRequest:
            pass
        r = FakeRequest()
        r.headers = {}
        auth(r)
        self.assertEqual(r.headers, {"Authorization": "Bearer abc"})



