import json
import urllib
import datetime
import requests
from requests.auth import AuthBase

from . import configuration, const

class EgnyteException(Exception):
    pass

class AuthorizationException(EgnyteException):
    pass

class RequestsAuth(AuthBase):
    """
    Sending oAuth access_token in auth header
    """
    def __init__(self, access_token):
        self.access_token = access_token

    def _oauth_str(self):
        """Returns oAuth string."""
        return 'Bearer %s' % self.access_token

    def __call__(self, r):
        r.headers['Authorization'] = self._oauth_str()
        return r

class Base(object):
    def __init__(self, config=None):
        if not isinstance(config, dict):
            config = configuration.load(config)
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
            client_id = self.config['api_key'],
            username = self.config['login'],
            password = self.config['password'],
            grant_type = self.GRANT_TYPE,
        )
        r = requests.post(url, data=data)
        if r.status_code == 200:
            return r.json()['access_token']
        elif r.status_code == 429:
            raise AuthorizationException('Access Token is already generated. Please try after sometime.')
        else:
            raise AuthorizationException('Failed to generate Access Token: %s' % r.text)
    
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
    ITER_CHUNK_SIZE = 10 * 1024 # bytes

    def __init__(self, config):
        super(EgnyteClient, self).__init__(config)
        self.auth = RequestsAuth(config['access_token'])

    def encode_path(self, path):
        return str(urllib.quote(path.encode('utf-8'), '/'))

    def userinfo(self):
        headers = {'content-type': 'application/json'}
        url = self.get_url(self.USER_INFO_URI)
        r = requests.get(url, auth=self.auth, headers=headers)
        return r

    def create_folder(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        folderpath = self.encode_path(folderpath)
        data = {'action': self.ACTION_ADD_FOLDER}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        ## make sure that success code here is 201
        return r

    def get_file(self, filepath, fptr):
        url = self.get_url(self.FILE_URI, filepath=self.encode_path(filepath))
        r = requests.get(url, auth=self.auth, stream=True)
        if r.status_code == requests.codes.ok:
            for data in r.iter_content(self.ITER_CHUNK_SIZE):
                fptr.write(data)
        return r

    def put_file(self, filepath, fptr):
        url = self.get_url(self.FILE_URI, filepath=self.encode_path(filepath))
        r = requests.post(url, auth=self.auth, data=fptr, stream=True)
        return r

    def delete(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        r = requests.delete(url, auth=self.auth)
        return r

    def move(self, folderpath, destination):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        data = {'action': self.ACTION_MOVE, 'destination': destination}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        return r

    def copy(self, folderpath, destination):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        data = {'action': self.ACTION_COPY, 'destination': destination}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        return r

    def list_content(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=self.encode_path(folderpath))
        data = {'action': self.ACTION_LIST}
        headers = {'content-type': 'application/json'}
        r = requests.get(url, auth=self.auth, data=json.dumps(data), headers=headers)
        return r

    def create_link(self, path, kind, accessibility,
                    recipients=None, send_email=None, message=None,
                    copy_me=None, notify=None, link_to_current=None,
                    expiry=None, add_filename=None,
                    ):
        assert kind in const.LINK_KIND_LIST
        assert accessibility in const.LINK_ACCESSIBILITY_LIST
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
        if kind == const.LINK_KIND_FILE and link_to_current is not None:
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
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        return r

    def delete_link(self, id):
        url = self.get_url(self.LINK_URI2, id=id)
        r = requests.delete(url, auth=self.auth)
        return r

    def link_details(self, id):
        url = self.get_url(self.LINK_URI2, id=id)
        r = requests.get(url, auth=self.auth)
        return r

    def links(self):
        ## TODO
        pass
