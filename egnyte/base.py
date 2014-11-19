import json
import time
import hashlib

from six import string_types
from six.moves.urllib.parse import quote

import requests

from egnyte.configuration import load
from egnyte.exc import default

JSON_HEADERS = {'content-type': 'application/json'}

class Const:
    LINK_KIND_FILE = "file"
    LINK_KIND_FOLDER = "folder"
    LINK_KIND_LIST = (LINK_KIND_FILE, LINK_KIND_FOLDER)

    LINK_ACCESSIBILITY_ANYONE = "anyone"  # accessible by anyone with link
    LINK_ACCESSIBILITY_PASSWORD = "password"  # accessible by anyone with link
    # who knows password
    LINK_ACCESSIBILITY_DOMAIN = "domain"  # accessible by any domain user
    # (login required)
    LINK_ACCESSIBILITY_RECIPIENTS = "recipients"  # accessible by link recipients,
    # who must be domain users
    # (login required)
    LINK_ACCESSIBILITY_LIST = (
        LINK_ACCESSIBILITY_ANYONE,
        LINK_ACCESSIBILITY_PASSWORD,
        LINK_ACCESSIBILITY_DOMAIN,
        LINK_ACCESSIBILITY_RECIPIENTS,
    )
    USER_INFO_URI = "pubapi/v1/userinfo"
    FOLDER_URI = "pubapi/v1/fs%(folderpath)s"
    FILE_URI = "pubapi/v1/fs-content%(filepath)s"
    FILE_URI_CHUNKED = "pubapi/v1/fs-content-chunked%(filepath)s"
    LINK_URI = "pubapi/v1/links"
    LINK_URI2 = "pubapi/v1/links/%(id)s"

    ACTION_ADD_FOLDER = 'add_folder'
    ACTION_MOVE = 'move'
    ACTION_COPY = 'copy'


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
        if 'headers' in kwargs:
            headers.update(kwargs.pop('headers'))
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
        if hasattr(self, '_session'):
            self._session.close()
            del self._session

class HasClient(object):
    """Base wrapper for API resources"""

    def __init__(self, _client, **kwargs):
        self._client = _client
        self.__dict__.update(kwargs)

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

class _FileChunk(object):
    """Wrapped for chunk of the file that also calculates SHA256 checksum while file is read"""
    def __init__(self, fp, start, size):
        self.fp = fp
        self.position = start
        self.left = self.size = size
        self.sha = hashlib.sha512()

    def read(self, size=None):
        if size is None or size > self.left:
            size = self.left
        result = self.fp.read(size)
        self.sha.update(result)
        self.left -= len(result)
        return result

    def rewind(self):
        self.fp.seek(self.position)
        self.left = self.size
        self.sha = hashlib.sha512()

def split_file_into_chunks(fp, file_size, chunk_size):
    """
    Split file-like object into sequence of file-like objects, each of
    those with size no greater than chunk_size bytes.
    Those are just wrappers to the original file-like objects. They should be fully
    read sequentially, and they cannot be used concurrently with
    the original object.
    """
    position = 0
    while position < file_size:
        yield _FileChunk(fp, position, min(chunk_size, file_size - position))
        position += chunk_size

def get_file_size(fp):
    """Get size of the file or length of a bytes object"""
    fp.seek(0, 2) # move the current position to the end of the file
    size = fp.tell()
    fp.seek(0,0) # move the current position to the beginning of the file
    return size

