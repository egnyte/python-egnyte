import unittest
import csv
from os import unlink
from egnyte import configuration, client
from tempfile import NamedTemporaryFile

CONFIG_NAME = 'test_config.json'

EXPECTED_FILES_TITLE = ['This report reflects activity up to 2/24/17 23:59:59']
EXPECTED_FILES_HEADER = ['File/Folder', "Target Path/Link", 'User/Location',
                         'User ID', 'Transaction Type', 'Action Info', 'Access', 'Time', 'IP Address',
                         'Device Name', 'File Version', 'Space Used']
EXPECTED_LOGINS_TITLE = [
    'This report reflects activity up to 2/24/17 23:59:59']
EXPECTED_LOGINS_HEADER = [
    'User Name', 'User ID', 'Event', 'IP Address', 'Access', 'Time', 'Logout Time']


class TestAudits(unittest.TestCase):

    def setUp(self):
        self.config = configuration.load(CONFIG_NAME)
        self.egnyte = client.EgnyteClient(self.config)
        self.temp_file = NamedTemporaryFile(delete=False)

    def tearDown(self):
        unlink(self.temp_file.name)
        self.egnyte.close()
        del self.egnyte

    def test_create_and_download_files_audit_report_in_csv(self):
        audit_report = self.egnyte.audits.files(
            'csv', '2017-02-20', '2017-02-24')

        audit_report.wait()

        downloaded_file = audit_report.download()
        downloaded_file.save_to(self.temp_file.name)

        rows = self.__read_csv_file(self.temp_file.name)
        self.temp_file.close()

        self.assertEqual(EXPECTED_FILES_TITLE, rows[0])
        self.assertEqual(EXPECTED_FILES_HEADER, rows[1])

    def test_create_and_download_logins_report_in_csv(self):
        audit_report = self.egnyte.audits.logins(
            'csv', '2017-02-20', '2017-02-24', ['logins'])

        audit_report.wait()

        download_file = audit_report.download()
        download_file.save_to(self.temp_file.name)

        rows = self.__read_csv_file(self.temp_file.name)
        self.temp_file.close()

        self.assertEqual(EXPECTED_LOGINS_TITLE, rows[0])
        self.assertEqual(EXPECTED_LOGINS_HEADER, rows[1])

    def __read_csv_file(self, file_path):
        rows = []
        with open(file_path, 'r') as csvfile:
            reader = csv.reader(csvfile)
            for row in reader:
                rows.append(row)
        return rows
