import json
import urllib
import requests
from requests.auth import AuthBase

from . import const

class EgnyteOAuth(AuthBase):
    """
    Sending oAuth access_token in auth header
    """
    def __init__(self, access_token):
        self.access_token = access_token

    def __call__(self, r):
        r.headers['Authorization'] = _outh_str(self.access_token)
        return r

class Egnyte(object):
    def __init__(self, domain, access_token=None, username=None, password=None, api_key=None):
        self.domain = domain
        if access_token is None:
            access_token = self.get_access_token(username, password, api_key)
        self.auth = self.get_auth_obj(access_token)

    def get_access_token(self, username, password, api_key):
        url = const.ACCESS_TOKEN_URL % self.__dict__
        data = dict(
            client_id = api_key,
            username = username,
            password = password,
            grant_type = "password",
            )
        r = requests.post(url, data=data)
        if r.status_code == requests.codes.ok: #200
            return r.json()['access_token']
        return None

    def get_auth_obj(self, access_token):
        return EgnyteOAuth(access_token)

    def get_userinfo(self):
        headers = {'content-type': 'application/json'}
        url = const.USER_INFO_URL % self.__dict__
        r = requests.get(url, auth=self.auth, headers=headers)
        return r.json()

    def _get_folder_url(self, folderpath):
        return const.FOLDER_URL % {
            'domain': self.domain,
            'folderpath': str(urllib.quote(folderpath.encode('utf-8'), '/'))
            }
        
    def create_folder(self, folderpath):
        url = self._get_folder_url(folderpath)
        data = {'action': 'add_folder'}
        headers = {'content-type': 'application/json'}
        r = requests.post(url, auth=self.auth, data=json.dumps(data), headers=headers)
        return r

    def delete_folder(self, folderpath):
        url = self._get_folder_url(folderpath)
        r = requests.delete(url, auth=self.auth)
        return r
        
        
