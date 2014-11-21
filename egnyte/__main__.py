#!/usr/bin/env python
from __future__ import print_function

import getpass
import argparse
import json
import sys
import datetime
import codecs
from contextlib import closing

from egnyte import client, configuration, exc, base

parser = argparse.ArgumentParser(prog="python -m egnyte")
parser.add_argument("-c", "--config-path", help="Path to config file")

subparsers = parser.add_subparsers()

parser_config = subparsers.add_parser('config', help='commands related to configuration')
subparsers_config = parser_config.add_subparsers()

parser_config_show = subparsers_config.add_parser('show', help="show configuration")
parser_config_show.set_defaults(command="config_show")

parser_config_create = subparsers_config.add_parser('create', help='create a new configuration file')
parser_config_create.set_defaults(command="config_create")

parser_config_update = subparsers_config.add_parser('update', help='update a configuration file')
parser_config_update.set_defaults(command="config_update")

parser_config_token = subparsers_config.add_parser('token', help='generate a new access token and store it in config file')
parser_config_token.set_defaults(command="config_token")

parser_token = subparsers.add_parser('token', help='generate a new access token and print it')
parser_token.set_defaults(command='token')

parser_test = subparsers.add_parser('test', help='test if config is correct (connects to service)')
parser_test.set_defaults(command='test')

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

# Audit generator

parser_audit = subparsers.add_parser('audit', help='generate audit reports')
subparsers_audit = parser_audit.add_subparsers()

parser_audit_files = subparsers_audit.add_parser('files', help="create Files report")
parser_audit_files.set_defaults(command="audit_files")

parser_audit_logins = subparsers_audit.add_parser('logins', help="create Logins report")
parser_audit_logins.set_defaults(command="audit_logins")

parser_audit_permissions = subparsers_audit.add_parser('permissions', help="create Permissions report")
parser_audit_permissions.set_defaults(command="audit_permissions")

parser_audit_get = subparsers_audit.add_parser('get', help="get a previously generated report")
parser_audit_get.set_defaults(command="audit_get")

# Common options
for p in (parser_audit_files, parser_audit_logins, parser_audit_permissions, parser_audit_get):
    p.add_argument('--save', required=False, default=None, help="File to save to the report to (default is standard output)")

for p in (parser_audit_files, parser_audit_logins, parser_audit_permissions):
    p.add_argument('--format', required=False, default="csv", help="Report type (json or csv. Default is csv)")
    p.add_argument('--start', required=False, default='yesterday', help='Start date (YYYY-MM-DD)')
    p.add_argument('--end', required=False, default='today', help='End date (YYYY-MM-DD)')


parser_audit_files.add_argument('--folder', required=False, action='append', default=None, help="Absolute folder path for the destination folder. 'folder' or 'file' is required. Can be used multiple times")
parser_audit_files.add_argument('--file', required=False, default=None, help="Absolute folder path for the destination file, wildcards allowed. 'folder' or 'file' is required")
parser_audit_files.add_argument('--users', required=False, default=None, help='Users to report on (comma separated list, default is all)')
parser_audit_files.add_argument('--transaction_type', required=False, default=None, help="""
Transaction type: upload, download, preview, delete, copy, move, restore_trash, delete_trash, create_link, delete_link, download_link
(comma separated list, default is all""")

parser_audit_logins.add_argument('--events', required=True, help="Event types: logins, logouts, account_lockouts, password_resets, failed_attempts (comma separated list)")
parser_audit_logins.add_argument('--access-points', required=False, default=None, help="Access points to cover: Web, FTP, Mobile (comma separated list, default is all)")
parser_audit_logins.add_argument('--users', required=False, default=None, help='Users to report on (comma separated list, default is all)')

parser_audit_permissions.add_argument('--assigners', required=True, help='Permission assigners (comma separated list)')
parser_audit_permissions.add_argument('--folder', required=True, action='append', default=None, help="Absolute folder path for the destination folder. Can be used multiple times")
parser_audit_permissions.add_argument('--users', required=False, default=None, help='Users to report on (comma separated list)')
parser_audit_permissions.add_argument('--groups', required=False, default=None, help='Groups to report on (comma separated list)')

parser_audit_get.add_argument('--id', required=True, help="Id of the report")

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

    def common_audit_args(self):
        format = self.args.format
        date_start = self.date(self.args.start)
        date_end = self.date(self.args.end)
        return (format, date_start, date_end)

    def date(self, value):
        """Poor mans human readable dates"""
        if value == 'today':
            return datetime.date.today()
        elif value == 'yesterday':
            return datetime.date.today() - datetime.timedelta(days=1)
        else:
            return datetime.date.datetime.strptime(value, "%Y-%m-%d").date()

    def wait_and_save_report(self, report):
        if self.args.save:
            output = open(self.args.save, "wb")
            print("Opened %s for writing, requesting report")
            with closing(output):
                report.wait()
                report.download().write_to(output)
        else:
            report.wait()
            download = report.download()
            with closing(download):
                lines = codecs.iterdecode(iter(download), 'UTF-8')
                for line in lines:
                    print(line)

    def comma_split(self, param):
        value = getattr(self.args, param, None)
        if value:
            return value.split(',')

    def cmd_audit_get(self):
        audits = client.EgnyteClient(self.config).audits
        report = audits.get(id = self.args.id)
        return self.wait_and_save_report(report)

    def cmd_audit_files(self):
        audits = client.EgnyteClient(self.config).audits
        folders = getattr(self.args, 'folder', None)
        file = self.args.file
        users = self.comma_split('users')
        transaction_type = self.comma_split('transaction_type')
        report = audits.files(*self.common_audit_args(), folders=folders, file=file, users=users, transaction_type=transaction_type)
        return self.wait_and_save_report(report)

    def cmd_audit_permissions(self):
        audits = client.EgnyteClient(self.config).audits
        assigners = self.comma_split('assigner')
        folders = self.args.folder
        users = self.comma_split('users')
        groups = self.comma_split('groups')
        report = audits.permissions(*self.common_audit_args(), assigners=assigners, folders=folders, users=users, groups=groups)
        return self.wait_and_save_report(report)

    def cmd_audit_logins(self):
        audits = client.EgnyteClient(self.config).audits
        users = self.comma_split('users')
        events = self.comma_split('events')
        access_points = self.comma_split('access_points')
        report = audits.logins(*self.common_audit_args(), events=events, access_points=access_points, users=users)
        return self.wait_and_save_report(report)

def main():
    parsed = parser.parse_args()
    sys.exit(Commands(parsed).run())

if __name__ == '__main__':
    main()
