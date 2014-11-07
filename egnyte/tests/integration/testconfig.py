import json
import os
import os.path
import unittest

try:
    filepath = os.path.join(os.path.expanduser('~'), '.egnyte', 'test_config.json')
    with file(filepath, "r") as fp:
        config = json.load(fp)

    class TestCase(unittest.TestCase):
        USERNAME = config['username']
        PASSWORD = config['password']
        DOMAIN = config['domain']
        API_KEY = config['api_key']
        ACCESS_TOKEN = config['access_token']

except Exception:

    @unittest.skip("No configuration for integration tests, check README.md")
    class TestCase(unittest.TestCase):
        USERNAME = ''
        PASSWORD = ''
        DOMAIN = ''
        API_KEY = ''
        ACCESS_TOKEN = ''

    

