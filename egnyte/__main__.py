#!/usr/bin/env python
from __future__ import print_function

import getpass
import argparse
import json
import sys

from egnyte import client, configuration

parser = argparse.ArgumentParser(prog="python -m egnyte")
parser.add_argument("-c", "--config-path", help="Path to config file")

subparsers = parser.add_subparsers()

parser_config = subparsers.add_parser('config', help='commands related to configuration')

parser_token = subparsers.add_parser('token', help='generate a new access token and print it')
parser_token.set_defaults(command='token')

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
    p.add_argument('-l', '--login', required=required, help='login')
    p.add_argument('-p', '--password', required=required, help='password')
    p.add_argument('-k', '--key', dest='api_key', required=required, help='API key')

for p in (parser_config_create, parser_config_update):
    p.add_argument('-t', '--token', dest='access_token', required=False, help='API access token')


class Commands(object):
    _config = None
    config_keys = ('login', 'password', 'domain', 'api_key', 'access_token')

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
        method = getattr(self, "cmd_%s" % self.args.command, None)
        if method is not None:
            method()
        else:
            print("Command '%s' not implemented yet" % self.args.command.replace('_', ' '))
            sys.exit(1)

    def get_access_token(self):
        config = self.require_password()
        try:
            return client.EgnyteOAuth(config).get_access_token()
        except client.EgnyteException as e:
            print(str(e))
            sys.exit(2)

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
        self.config.clear()
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


def main():
    parsed = parser.parse_args()
    Commands(parsed).run()

if __name__ == '__main__':
    main()