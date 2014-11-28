from __future__ import print_function

import datetime

from egnyte import exc
from egnyte.tests.config import IntegrationCase


class TestNotes(IntegrationCase):
    def test_notes(self):
        folder = self.root_folder.folder('notes')
        folder.create(True)

        f = folder.file('test.txt')
        f.upload(b'foobar')

        try:
            note = f.add_note("this is a test message")
            all = self.client.notes.list()
            self.assertIn(note, all)
            self.assertEqual(f, note.get_file())
            notes = f.get_notes()
            self.assertEqual(tuple(notes), (note,))
            note.delete()
            notes = f.get_notes()
            self.assertEqual(tuple(notes), ())
            all = self.client.notes.list()
            self.assertNotIn(note, all)
        finally:
            f.delete()
