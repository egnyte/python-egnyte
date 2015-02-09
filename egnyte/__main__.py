#!/usr/bin/env python
from __future__ import print_function, unicode_literals

import getpass
import argparse
import json
import sys
import datetime
import codecs
from contextlib import closing

from egnyte import client, configuration, exc, base


parser_kwargs = dict(formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=50))


def create_main_parser():
    main = argparse.ArgumentParser(prog="python -m egnyte", **parser_kwargs)
    main.add_argument("-c", "--config-path", help="Path to config file")
    main.add_argument('-v', '--verbose', action='count', dest='verbosity', help="Be more verbose. Can be repeated for debugging", default=0)
    main.add_argument('--impersonate', metavar="USERNAME", help="Impersonate another user (username or email)", default=None)

    subparsers = main.add_subparsers()

    parser_config = subparsers.add_parser('config', help='commands related to configuration', **parser_kwargs)
    subparsers_config = parser_config.add_subparsers()

    parser_config_show = subparsers_config.add_parser('show', help="show configuration", **parser_kwargs)
    parser_config_show.set_defaults(command="config_show")

    parser_config_create = subparsers_config.add_parser('create', help='create a new configuration file', **parser_kwargs)
    parser_config_create.set_defaults(command="config_create")

    parser_config_update = subparsers_config.add_parser('update', help='update a configuration file', **parser_kwargs)
    parser_config_update.set_defaults(command="config_update")

    parser_config_token = subparsers_config.add_parser('token', help='generate a new access token and store it in config file', **parser_kwargs)
    parser_config_token.set_defaults(command="config_token")

    parser_token = subparsers.add_parser('token', help='generate a new access token and print it', **parser_kwargs)
    parser_token.set_defaults(command='token')

    parser_test = subparsers.add_parser('test', help='test if config is correct (connects to service)', **parser_kwargs)
    parser_test.set_defaults(command='test')

    for parser, required in [(parser_config_create, True), (parser_config_update, False), (parser_token, False)]:
        parser.add_argument('-d', '--domain', required=required, help='domain name')
        parser.add_argument('-l', '--login', required=False, help='login')
        parser.add_argument('-p', '--password', required=False, help='password')
        parser.add_argument('-k', '--key', dest='api_key', required=required, help='API key')

    for parser in (parser_config_create, parser_config_update):
        parser.add_argument('-t', '--token', dest='access_token', required=False, help='API access token')

    # Audit generator

    parser_audit = subparsers.add_parser('audit', help='generate audit reports', **parser_kwargs)
    subparsers_audit = parser_audit.add_subparsers()

    parser_audit_files = subparsers_audit.add_parser('files', help="create Files report", **parser_kwargs)
    parser_audit_files.set_defaults(command="audit_files")

    parser_audit_logins = subparsers_audit.add_parser('logins', help="create Logins report", **parser_kwargs)
    parser_audit_logins.set_defaults(command="audit_logins")

    parser_audit_permissions = subparsers_audit.add_parser('permissions', help="create Permissions report", **parser_kwargs)
    parser_audit_permissions.set_defaults(command="audit_permissions")

    parser_audit_get = subparsers_audit.add_parser('get', help="get a previously generated report", **parser_kwargs)
    parser_audit_get.set_defaults(command="audit_get")

    # Common options
    for parser in (parser_audit_files, parser_audit_logins, parser_audit_permissions, parser_audit_get):
        parser.add_argument('--save', required=False, default=None, help="File to save to the report to (default is standard output)")

    for parser in (parser_audit_files, parser_audit_logins, parser_audit_permissions):
        parser.add_argument('--format', required=False, default="csv", help="Report type (json or csv. Default is csv)")
        parser.add_argument('--start', required=False, default='yesterday', help='Start date (YYYY-MM-DD)')
        parser.add_argument('--end', required=False, default='today', help='End date (YYYY-MM-DD)')

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

    parser_audit_get.add_argument('--id', type=int, required=True, help="Id of the report")

    parser_upload = subparsers.add_parser('upload', help='send files to Egnyte', **parser_kwargs)
    parser_upload.set_defaults(command="upload")

    parser_upload.add_argument('paths', nargs='+', help="Paths (files to directories) to upload")
    parser_upload.add_argument('target', help="Path in Cloud File System to upload to")
    parser_upload.add_argument('-x', '--exclude', action='append', default=None, help='Exclude items that match this glob pattern')

    parser_download = subparsers.add_parser('download', help='download files from Egnyte', **parser_kwargs)
    parser_download.set_defaults(command="download")

    parser_download.add_argument('paths', nargs='+', help="Paths (files to directories) to download")
    parser_download.add_argument('--target', help="Local directory to put downloaded files and directories in", default='.')
    parser_download.add_argument('--overwrite', action='store_const', const=True, default=False, help="Delete local files and directories that conflict with cloud content")

    parser_settings = subparsers.add_parser('settings', help='show domain settings', **parser_kwargs)
    parser_settings.set_defaults(command="settings")

    parser_search = subparsers.add_parser('search', help='search for files', **parser_kwargs)
    parser_search.set_defaults(command="search")
    parser_search.add_argument('query', help='Search query')
    parser_search.add_argument('--mtime_from', help="Minimim modification date", default=None)
    parser_search.add_argument('--mtime_to', help="Maximum modification date", default=None)
    parser_search.add_argument('--folder', help="Limit search to a specified folder", default=None)

    parser_events = subparsers.add_parser('events', help='show events from the domain', **parser_kwargs)
    parser_events.set_defaults(command="events")
    parser_events.add_argument('--start', type=int, help="Starting event id. Default or 0 - last seen event. Negative numbers are counter backwards from last event", default=None)
    parser_events.add_argument('--stop', type=int, help="Stop event id. Default - poll indefinitely. 0 means last event. Negative numbers are counter backwards from last event", default=None)
    parser_events.add_argument('--type', action='append', help="Limit to events of specific type", default=None)
    parser_events.add_argument('--folder', help="Limit to events in specific folder and it's subfolders", default=None)
    parser_events.add_argument('--suppress', help="Skip events caused by this app or user. Valid values: app, user.", default=None)





    return main

def to_json(obj):
    return {k:v for (k, v) in obj.__dict__.items() if not k.startswith('_')}

class Commands(object):
    _config = None
    config_keys = ('login', 'password', 'domain', 'api_key', 'access_token')
    STATUS_CMD_NOT_FOUND = 1
    STATUS_API_ERROR = 2
    INFO = 1
    DEBUG = 2

    def load_config(self):
        if self._config is None:
            self._config = configuration.load(self.args.config_path)
        return self._config

    def save_config(self):
        return configuration.save(self.config, self.args.config_path)

    config = property(load_config)

    def __init__(self, args):
        self.args = args

    @property
    def info(self):
        """If verbosity is INFO or better"""
        return self.args.verbosity >= self.INFO

    @property
    def debug(self):
        """If verbosity is INFO or better"""
        return self.args.verbosity >= self.DEBUG

    def run(self):
        if not hasattr(self.args, 'command'):
            print("Use -h or --help for help")
            return

        method = getattr(self, "cmd_%s" % self.args.command, None)
        if self.debug:
            print("running %s" % method.__name__)
        if method is None:
            print("Command '%s' not implemented yet" % self.args.command.replace('_', ' '))
            return self.STATUS_CMD_NOT_FOUND
        try:
            return method()
        except exc.EgnyteError as e:
            if self.debug:
                raise
            print(repr(e))
            return self.STATUS_API_ERROR

    def get_client(self):
        result = client.EgnyteClient(self.config)
        if self.args.impersonate is not None:
            result.impersonate(self.args.impersonate)
        return result

    def get_access_token(self):
        config = self.require_password()
        return base.get_access_token(config)

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

    def print_json(self, obj):
        print(json.dumps(obj, indent=2, sort_keys=True, default=to_json))

    def cmd_config_show(self):
        self.print_json(self.config)

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
        api = self.get_client()
        info = api.user_info()
        print("Connection successful for user %s" % (info['username'],))

    def cmd_search(self):
        api = self.get_client()
        results = api.search.files(self.args.query, modified_before=self.args.mtime_to, modified_after=self.args.mtime_from, folder=self.args.folder)
        self.print_json(results)


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
        api = self.get_client()
        audits = api.audits
        report = audits.get(id=self.args.id)
        return self.wait_and_save_report(report)

    def cmd_audit_files(self):
        api = self.get_client()
        audits = api.audits
        folders = getattr(self.args, 'folder', None)
        file = self.args.file
        users = self.comma_split('users')
        transaction_type = self.comma_split('transaction_type')
        report = audits.files(*self.common_audit_args(), folders=folders, file=file, users=users, transaction_type=transaction_type)
        return self.wait_and_save_report(report)

    def cmd_audit_permissions(self):
        api = self.get_client()
        audits = api.audits
        assigners = self.comma_split('assigner')
        folders = self.args.folder
        users = self.comma_split('users')
        groups = self.comma_split('groups')
        report = audits.permissions(*self.common_audit_args(), assigners=assigners, folders=folders, users=users, groups=groups)
        return self.wait_and_save_report(report)

    def cmd_audit_logins(self):
        api = self.get_client()
        audits = api.audits
        users = self.comma_split('users')
        events = self.comma_split('events')
        access_points = self.comma_split('access_points')
        report = audits.logins(*self.common_audit_args(), events=events, access_points=access_points, users=users)
        return self.wait_and_save_report(report)

    def transfer_callbacks(self):
        if self.info:
            if sys.stdout.isatty():
                result = TerminalCallbacks()
                if self.debug:
                    result.force_newline = True
                return result
            else:
                return VerboseCallbacks()

    def cmd_upload(self):
        api = self.get_client()
        api.bulk_upload(self.args.paths, self.args.target, self.args.exclude, self.transfer_callbacks())

    def cmd_download(self):
        api = self.get_client()
        api.bulk_download(self.args.paths, self.args.target, self.args.overwrite, self.transfer_callbacks())

    def cmd_settings(self):
        self.print_json(self.get_client().settings)

    def cmd_events(self):
        start = self.args.start
        stop = self.args.stop
        events = self.get_client().events
        if start is None:
            start = events.latest_event_id
        elif start <= 0:
            start = events.latest_event_id + start
        if stop is not None and stop <= 0:
            stop = events.latest_event_id + stop
        events = events.filter(start_id = start, suppress=self.args.suppress, folder=self.args.folder, types=self.args.type or None)
        try:
            for event in events:
                self.print_json(event)
                print()
                if stop is not None and event.id >= stop:
                    break
        except KeyboardInterrupt:
            pass


class VerboseCallbacks(client.ProgressCallbacks):
    """Progress callbacks used when sys.stdout is a file or a pipe"""

    def write(self, text, force_newline=False):
        print(text)

    def getting_info(self, cloud_path):
        self.write("Getting info about %s" % cloud_path)

    def got_info(self, cloud_obj):
        self.write("Got info about %s" % cloud_obj.path)

    def download_start(self, local_path, cloud_file, size):
        self.write("Downloading %s" % local_path)
        self.current = local_path

    def upload_start(self, local_path, cloud_file, size):
        self.write("Uploading %s" % local_path)
        self.current = local_path

    def creating_directory(self, cloud_folder):
        self.write("Creating directory %s" % cloud_folder.path)

    def skipped(self, cloud_obj, reason):
        self.write("Skipped %s: %s" % (cloud_obj.path, reason), force_newline=True)

    def finished(self):
        self.write("Finished", force_newline=True)


class TerminalCallbacks(VerboseCallbacks):
    """Progress callbacks used when sys.stdout is a terminal"""
    force_newline = False

    def __init__(self):
        self.last_len = 0

    def write(self, text, force_newline=None):
        if force_newline is None:
            force_newline = self.force_newline
        output = ["\r"]
        sys.stdout.write("\r")  # return the carret
        if len(text) < self.last_len:  # clear out previous text
            sys.stdout.write(' ' * self.last_len)
            sys.stdout.write("\r")  # return the carret
        output.append(text)
        if force_newline:
            output.append('\n')
        sys.stdout.write("".join(output))
        sys.stdout.flush()
        self.last_len = len(text)

    def download_progress(self, cloud_file, size, downloaded):
        self.write("Downloading %s, %d%% complete" % (self.current, (downloaded * 100) / size))

    def upload_progress(self, cloud_file, size, uploaded):
        self.write("Uploading %s, %d%%" % (self.current, (uploaded * 100) / size))

    def download_finish(self, cloud_file):
        self.write("Downloaded %s" % self.current)

    def upload_finish(self, cloud_file):
        self.write("Uploaded %s" % self.current)


def main():
    parsed = create_main_parser().parse_args()
    sys.exit(Commands(parsed).run())

def full_help():
    parser = create_main_parser()
    return parser.format_help()

if __name__ == '__main__':
    main()
