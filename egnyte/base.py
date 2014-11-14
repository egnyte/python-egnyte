from __future__ import print_function

import json
import time

from six import string_types
from six.moves.urllib.parse import quote

import requests

from egnyte.configuration import load
from egnyte.exc import default

JSON_HEADERS = {'content-type': 'application/json'}

class Session(object):
    """
    Provides persistent HTTPS connections to Egnyte API
    """
    time_between_requests = None
    last_request_time = None

    def __init__(self, config=None):
        self.config = config if isinstance(config, dict) else load(config)
        domain = self.config['domain']
        if '.' not in domain:
            domain = domain + ".egnyte.com"
        self._url_prefix = "https://%s/" % domain
        self._session = requests.Session()
        if 'access_token' in self.config:
            self._session.headers['Authorization'] = 'Bearer %s' % self.config['access_token']
        if 'time_between_requests' in self.config:
            self.time_between_requests = config['time_between_requests']
        elif 'requests_per_second' in self.config:
            self.time_between_requests = 1.0 / float(self.config['requests_per_second'])

    def _encode_path(self, path):
        return quote(path, '/')

    def _respect_limits(self):
        if self.time_between_requests:
            if self.last_request_time is not None:
                since = time.time() - self.last_request_time
                if since < self.time_between_requests:
                    time.sleep(self.time_between_requests - since)
            self.last_request_time = time.time()

    def GET(self, url, **kwargs):
        self._respect_limits()
        return self._session.get(url, **kwargs)

    def POST(self, url, json_data=None, **kwargs):
        self._respect_limits()
        if json_data is None:
            headers = {}
            data = kwargs.pop('data', None)
        else:
            headers = JSON_HEADERS
            data = json.dumps(json_data)
        return self._session.post(url, data=data, headers=headers, **kwargs)

    def DELETE(self, url, **kwargs):
        self._respect_limits()
        return self._session.delete(url, **kwargs)

    def get_url(self, path, **kw):
        if kw:
            kw = {k:self._encode_path(v) if isinstance(v, string_types) else str(v) for k, v in kw.items()}
            return self._url_prefix + path % kw
        else:
            return self._url_prefix + path

    def close(self):
        print("%r.close called" % self)
        if hasattr(self, '_session'):
            self._session.close()
            del self._session


def get_access_token(config):
    session = Session(config)
    url = session.get_url("puboauth/token")
    data = dict(
        client_id=config['api_key'],
        username=config['login'],
        password=config['password'],
        grant_type="password",
    )
    return default.check_json_response(session.POST(url, data))['access_token']

class HasClient(object):
    """Base wrapper for API resources"""

    def __init__(self, _client, **kwargs):
        self._client = _client
        self.__dict__.update(kwargs)


