#!/usr/bin/env python
from __future__ import print_function

import getpass
import argparse
import json
import sys

from egnyte import client, configuration, exc, base

parser = argparse.ArgumentParser(prog="python -m egnyte")
parser.add_argument("-c", "--config-path", help="Path to config file")

subparsers = parser.add_subparsers()

parser_config = subparsers.add_parser('config', help='commands related to configuration')

parser_token = subparsers.add_parser('token', help='generate a new access token and print it')
parser_token.set_defaults(command='token')

parser_test = subparsers.add_parser('test', help='test if config is correct (connects to service)')
parser_test.set_defaults(command='test')

subparsers_config = parser_config.add_subparsers()

parser_config_show = subparsers_config.add_parser('show', help="show configuration")
parser_config_show.set_defaults(command="config_show")

parser_config_create = subparsers_config.add_parser('create', help='create a new configuration file')
parser_config_create.set_defaults(command="config_create")

parser_config_update = subparsers_config.add_parser('update', help='update a configuration file')
parser_config_update.set_defaults(command="config_update")

parser_config_token = subparsers_config.add_parser('token', help='generate a new access token and store it in config file')
parser_config_token.set_defaults(command="config_token")


for p, required in [
        (parser_config_create, True),
        (parser_config_update, False),
        (parser_token, False),
    ]:
    p.add_argument('-d', '--domain', required=required, help='domain name')
    p.add_argument('-l', '--login', required=False, help='login')
    p.add_argument('-p', '--password', required=False, help='password')
    p.add_argument('-k', '--key', dest='api_key', required=required, help='API key')

for p in (parser_config_create, parser_config_update):
    p.add_argument('-t', '--token', dest='access_token', required=False, help='API access token')


class Commands(object):
    _config = None
    config_keys = ('login', 'password', 'domain', 'api_key', 'access_token')
    STATUS_CMD_NOT_FOUND = 1
    STATUS_API_ERROR = 2

    def load_config(self):
        if self._config is None:
            self._config = configuration.load(self.args.config_path)
        return self._config

    def save_config(self):
        return configuration.save(self.config, self.args.config_path)

    config = property(load_config)

    def __init__(self, args):
        self.args = args

    def run(self):
        if not hasattr(self.args, 'command'):
            print("Use -h or --help for help")
            return
        method = getattr(self, "cmd_%s" % self.args.command, None)
        if method is None:
            print("Command '%s' not implemented yet" % self.args.command.replace('_', ' '))
            return self.STATUS_CMD_NOT_FOUND
        try:
            return method()
        except exc.EgnyteError as e:
            print(repr(e))
            return self.STATUS_API_ERROR

    def get_access_token(self):
        config = self.require_password()
        return base.get_access_token(config).get_access_token()

    def merge_config(self):
        """Merge loaded config with command line params"""
        for key in self.config_keys:
            if getattr(self.args, key, None) is not None:
                self.config[key] = getattr(self.args, key)

    def require_password(self):
        """If config does not contain a password, ask user for it, but don't store it"""
        if self.config['password']:
            return self.config
        else:
            config = self.config.copy()
            config['password'] = getpass.getpass("Enter the password: ")
            return config

    def cmd_config_show(self):
        print(json.dumps(self.config, indent=2, sort_keys=True))

    def cmd_config_create(self):
        self._config = {}
        self.merge_config()
        self.save_config()

    def cmd_config_update(self):
        self.merge_config()
        self.save_config()

    def cmd_config_token(self):
        self.config['access_token'] = self.get_access_token()
        self.save_config()

    def cmd_token(self):
        self.merge_config()
        print(self.get_access_token())

    def cmd_test(self):
        api = client.EgnyteClient(self.config)
        info = api.user_info()
        print("Connection successful for user %s" % (info['username'],))

def main():
    parsed = parser.parse_args()
    sys.exit(Commands(parsed).run())

if __name__ == '__main__':
    main()
