import json
import urllib
import datetime
import requests
import requests.auth
import httplib
import contextlib

from egnyte.configuration import load


class Const:
    LINK_KIND_FILE = "file"
    LINK_KIND_FOLDER = "folder"
    LINK_KIND_LIST = [LINK_KIND_FILE, LINK_KIND_FOLDER, ]

    LINK_ACCESSIBILITY_ANYONE = "anyone"  # accessible by anyone with link
    LINK_ACCESSIBILITY_PASSWORD = "password"  # accessible by anyone with link
    # who knows password
    LINK_ACCESSIBILITY_DOMAIN = "domain"  # accessible by any domain user
    # (login required)
    LINK_ACCESSIBILITY_RECIPIENTS = "recipients"  # accessible by link recipients,
    # who must be domain users
    # (login required)
    LINK_ACCESSIBILITY_LIST = [
        LINK_ACCESSIBILITY_ANYONE,
        LINK_ACCESSIBILITY_PASSWORD,
        LINK_ACCESSIBILITY_DOMAIN,
        LINK_ACCESSIBILITY_RECIPIENTS,
    ]


class EgnyteException(Exception):
    pass


class InvalidRequest(EgnyteException):
    pass


class Forbidden(EgnyteException):
    pass


class NotFound(EgnyteException):
    pass


class ConnectionError(EgnyteException):
    pass


class AuthorizationRequired(EgnyteException):
    pass

class JsonParseError(EgnyteException):
    pass

default_error_mapping = {
    httplib.FORBIDDEN: Forbidden,
    httplib.UNAUTHORIZED: AuthorizationRequired,
    httplib.NOT_FOUND: NotFound
}

JSON_HEADERS = {'content-type': 'application/json'}


def oauth(access_token):
    """SendoAuth access_token in auth header"""
    header = 'Bearer %s' % access_token

    def add_header_to_request(request):
        request.headers['Authorization'] = header
        return request
    return add_header_to_request

def extract_errors(data):
    """Whoever came up with this inconsistent error data structure has too much imagination"""
    if 'errors' in data:
        data = data['errors']
    if 'inputErrors' in data:
        for err in extract_errors(data['inputErrors']):
            yield err
    elif hasattr(data, 'keys'):
            if 'code' in data:
                yield data
            else:
                for value in data.values():
                    for err in extract_errors(value):
                        yield err
    elif isinstance(data, list):
        for value in data:
            for err in extract_errors(value):
                yield err
    else:
        yield data

def check_response(response, *ok_statuses):
    if not len(ok_statuses): ok_statuses = (httplib.OK, )
    if response.status_code not in ok_statuses:
        error_type = default_error_mapping.get(response.status_code, EgnyteException)
        errors = []
        try:
            data = response.json()
            for err in extract_errors(data):
                errors.append(err)
        except Exception:
            errors.append({"http response": response.text})
        errors.append({"http status": response.status_code})
        raise error_type(*errors)
    return response

def check_json_response(response, *ok_statuses):
    try:
        return check_response(response, *ok_statuses).json()
    except ValueError:
        raise JsonParseError({"http response": response.text})


class Base(object):
    def __init__(self, config=None):
        if not isinstance(config, dict):
            config = load(config)
        self.config = config
        domain = self.config['domain']
        if '.' not in domain:
            domain = domain + ".egnyte.com"
        self._url_prefix = "https://%s/" % domain

    def get_url(self, path, **kw):
        return (self._url_prefix + path.lstrip('/')) % kw

class EgnyteOAuth(Base):
    ACCESS_TOKEN_URI = "/puboauth/token"
    GRANT_TYPE = "password"

    def get_access_token(self):
        url = self.get_url(self.ACCESS_TOKEN_URI)
        data = dict(
            client_id=self.config['api_key'],
            username=self.config['login'],
            password=self.config['password'],
            grant_type=self.GRANT_TYPE,
        )
        r = requests.post(url, data=data)
        return check_json_response(r)['access_token']


class EgnyteClient(Base):
    USER_INFO_URI = r"/pubapi/v1/userinfo"
    FOLDER_URI = r"/pubapi/v1/fs%(folderpath)s"
    FILE_URI = r"/pubapi/v1/fs-content/%(filepath)s"
    LINK_URI = r"/pubapi/v1/links"
    LINK_URI2 = r"/pubapi/v1/links/%(id)s"

    ACTION_ADD_FOLDER = 'add_folder'
    ACTION_MOVE = 'move'
    ACTION_COPY = 'copy'
    ACTION_LIST = 'list_content'
    ITER_CHUNK_SIZE = 16 * 1024  # bytes

    def GET(self, url, **kwargs):
        return requests.get(url, auth=self.auth, **kwargs)

    def POST(self, url, json_data=None, **kwargs):
        if json_data is None:
            headers = {}
            data = kwargs.pop('data', None)
        else:
            headers = JSON_HEADERS
            data = json.dumps(json_data)
        return requests.post(url, data=data, headers=headers, auth=self.auth, **kwargs)

    def DELETE(self, url, **kwargs):
        return requests.delete(url, auth=self.auth, **kwargs)

    def __init__(self, config):
        super(EgnyteClient, self).__init__(config)
        self.auth = oauth(config['access_token'])

    def encode_path(self, path):
        return str(urllib.quote(path.encode('utf-8'), '/'))

    def userinfo(self):
        return check_json_response(self.GET(self.get_url(self.USER_INFO_URI)))

    def create_folder(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        r = self.POST(url, {'action': self.ACTION_ADD_FOLDER})
        check_response(r, httplib.CREATED)

    def get_file(self, filepath):
        url = self.get_url(self.FILE_URI, filepath=self.encode_path(filepath))
        r = self.GET(url, stream=True)
        check_response(r)
        for data in r.iter_content(self.ITER_CHUNK_SIZE):
            yield data

    def put_file(self, filepath, fptr):
        url = self.get_url(self.FILE_URI, filepath=self.encode_path(filepath))
        r = self.POST(url, data=fptr, stream=True)
        check_response(r)

    def delete(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        r = self.DELETE(url)
        check_response(r)

    def move(self, folderpath, destination):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        data = {'action': self.ACTION_MOVE, 'destination': destination}
        r = self.POST(url, data)
        check_response(r)

    def copy(self, folderpath, destination):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        data = {'action': self.ACTION_COPY, 'destination': destination}
        r = self.POST(url, data)
        check_response(r)

    def list_content(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        #data = {'action': self.ACTION_LIST}
        r = self.GET(url)
        return check_json_response(r)

    def create_link(self, path, kind, accessibility,
                    recipients=None, send_email=None, message=None,
                    copy_me=None, notify=None, link_to_current=None,
                    expiry=None, add_filename=None,
                    ):
        assert kind in Const.LINK_KIND_LIST
        assert accessibility in Const.LINK_ACCESSIBILITY_LIST
        if recipients is None:
            recipients = []
        url = self.get_url(self.LINK_URI)
        data = {
            "path": path,
            "type": kind,
            "accessibility": accessibility,
        }
        if send_email is not None:
            data['sendEmail'] = send_email
        if copy_me is not None:
            data['copyMe'] = copy_me
        if notify is not None:
            data['notify'] = notify
        if add_filename is not None:
            data['addFilename'] = add_filename
        if kind == Const.LINK_KIND_FILE and link_to_current is not None:
            data["linkToCurrent"] = link_to_current
        if recipients:
            data['recipients'] = recipients
        if expiry is not None:
            if type(expiry) == int:
                data["expiryClicks"] = expiry
            elif type(expiry) == datetime.date:
                data["expiryDate"] = expiry.strftime("%Y-%m-%d")
        if message is not None:
            data['message'] = message
        r = self.POST(url, data)
        return check_json_response(r)

    def link_delete(self, id):
        url = self.get_url(self.LINK_URI2, id=id)
        r = self.DELETE(url)
        check_response(r)

    def link_details(self, id):
        url = self.get_url(self.LINK_URI2, id=id)
        r = self.GET(url)
        return check_json_response(r)

    def links(self):
        # TODO
        pass
