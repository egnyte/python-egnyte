import unittest

from egnyte import client, base, exc


class TestRequestsAuth(unittest.TestCase):
    def test_oauth(self):
        auth = base.oauth('abc')
        class FakeRequest:
            pass
        r = FakeRequest()
        r.headers = {}
        auth(r)
        self.assertEqual(r.headers, {"Authorization": "Bearer abc"})



