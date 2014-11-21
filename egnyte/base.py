import json
import time
import hashlib
from contextlib import closing

from six import string_types
from six.moves.urllib.parse import quote

import requests

from egnyte import exc, configuration

JSON_HEADERS = {'content-type': 'application/json'}


class Session(object):
    """
    Provides persistent HTTPS connections to Egnyte API
    """
    time_between_requests = None
    last_request_time = None

    def __init__(self, config=None):
        self.config = config if isinstance(config, dict) else configuration.load(config)
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
        return self._session.get(url, allow_redirects=False, **kwargs)

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

    def get_url(self, _path, **kwargs):
        if kwargs:
            kw = {k: self._encode_path(v) if isinstance(v, string_types) else str(v) for k, v in kwargs.items()}
            return self._url_prefix + _path % kw
        else:
            return self._url_prefix + _path

    def close(self):
        if hasattr(self, '_session'):
            self._session.close()
            del self._session


class HasClient(object):
    """Base class for API wrappers and utils"""

    def __init__(self, _client, **kwargs):
        self._client = _client
        self.__dict__.update(kwargs)


class Resource(object):
    """Base wrapper for API resources (singular objects with specific URL)"""
    _lazy_attributes = ()
    _url_template = ""  # Whatever this depends on should not be in _lazy_attributes

    def __init__(self, _client, **kwargs):
        self._client = _client
        self._modified = set()
        self.__dict__.update(kwargs)
        if '_url' not in kwargs:
            self._url = self._client.get_url(self._url_template, **kwargs)

    def __getattr__(self, name):
        """If attribute is in _lazyAtrributes yet we don't have it's value yet, fetch attributes from service."""
        if name in self._lazy_attributes:
            if name in self.__dict__:
                return self.__dict__[name]
        raise AttributeError(self, name)

    def _update_attributes(self, json_dict):
        for key in set(self._lazy_attributes).difference(self._modified):  # don't overwrite attributes modified by user
            if key in json_dict:
                self.__dict__[key] = json_dict[key]

    def _fetch_attributes(self):
        json = exc.default.check_json_response(self._client.GET(self._url))
        self._update_attributes(json)
        return json

    def __setattr__(self, name, value):
        """If attribute is in _lazy_attributes and new value is different than old one, mark attribute modified"""
        if name in self._lazy_attributes:
            old_value = getattr(self, name)
            if old_value == value:
                return
            self._modified.add(name)
        self.__dict__[name] = value

    def discard_changes(self):
        for key in self._modified:
            delattr(self, key)
        self._modified = set()

    def check(self):
        """
        Check if this object exists in the cloud and current user has read permissions on it.
        Will raise an exception otherwise.
        """
        self._fetch_attributes()

    def __str__(self):
        return "<%s: %s >" % (self.__class__.__name__, self._url)

    __repr__ = __str__


def get_access_token(config):
    session = Session(config)
    url = session.get_url("puboauth/token")
    data = dict(
        client_id=config['api_key'],
        username=config['login'],
        password=config['password'],
        grant_type="password",
    )
    return exc.default.check_json_response(session.POST(url, data))['access_token']


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
    fp.seek(0, 2)  # move the current position to the end of the file
    size = fp.tell()
    fp.seek(0, 0)  # move the current position to the beginning of the file
    return size

def date_format(date):
    return date.strftime("%Y-%m-%d")


class FileDownload(object):
    """
    Provides file length and other metadata.
    Delegates reads to underlying requests response.
    """

    def __init__(self, response):
        self.response = response

    def __len__(self):
        return int(self.response.headers['content-length'])

    def write_to(self, fp):
        """Copy data to a file, then close the source."""
        with closing(self):
            for chunk in self.iter_content():
                fp.write(chunk)

    def close(self):
        self.response.close()

    def closed(self):
        return self.response.closed()

    def read(self, amt=None, decode_content=True):
        """
        Wrap urllib3 response.
        amt - How much of the content to read. If specified, caching is skipped because it doesn't make sense to cache partial content as the full response.
        decode_content - If True, will attempt to decode the body based on the 'content-encoding' header.
        """
        return self.response.raw.read(amt, decode_content)

    def __iter__(self, **kwargs):
        """
        Iterate response body line by line.
        You can speficify alternate delimiter with delimiter parameter.
        """
        return self.response.iter_lines(**kwargs)

    def iter_content(self, chunk_size=16 * 1024):
        return self.response.iter_content(chunk_size)
