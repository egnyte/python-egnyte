#!/usr/bin/env python
import os
import getpass
import plac
import shelve

from egnyte import client

DEFAULT_SHELVE = os.path.expanduser('~/.egnyte/config.ini')

class EgnyteCMD(object):
    commands = 'init', 'show', 'get_access_token'

    @plac.annotations(
        username=("username", 'positional', None, str),
        domain=("domain", 'positional', None, str),
        api_key=("api_key", 'positional', None, str),
        token=("token", 'option', None, str),
        server=("server", 'option', None, str),
        )
    def init(self, username, domain, api_key, token=None, server="egnyte.com"):
        sh = shelve.open(DEFAULT_SHELVE)
        try:
            if token is None:
                token = self.get_access_token(username, domain, api_key, server)
            sh['config'] = {
                'username': username,
                'domain': domain,
                'server': server,
                'token': token,
                }
        finally:
            sh.close()

    def get_access_token(self, username, domain, api_key, server="egnyte.com"):
        password = getpass.getpass("Enter the password: ")
        oauth = client.EgnyteOAuth(
            domain,
            username,
            password,
            api_key,
            )
        r = oauth.get_access_token()
        if r.status_code == 200:
            data = r.json()
            token = data['access_token']
            print 'Access Token: ', token
        elif r.status_code == 429:
            print 'Access Token is already generated. Please try after sometime.'
        else:
            print 'Failed to generate Access Token: %s', r.data()
        return token

    def show(self):
        sh = shelve.open(DEFAULT_SHELVE)
        try:
            for k, v in sh['config'].items():
                print "%-10s => %s" % (k, v)
        finally:
            sh.close()


def main():
    plac.Interpreter.call(EgnyteCMD)

if __name__ == '__main__':
    main()