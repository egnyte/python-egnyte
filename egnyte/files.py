from contextlib import closing

from egnyte.base import HasClient, Const
from egnyte import links

class Item(HasClient):
    """
    File or folder.
    """

class File(Item):
    """
    Wrapper for a file in the cloud.
    Does not have to exist - can represent a new file to be uploaded.
    path - file path
    """

    def upload(self, fp, size=None):
        """
        Upload file contents.
        fp can be any file-like object, but if you don't specify it's size in
        advance it must support tell and seek methods.
        """
        return self._client.put_file_contents(self.path, fp, size)

    def download(self):
        """
        Download file contents.
        Returns a FileDownload.
        """
        return self._client.get_file_contents(self.path)

    def link(self, accessibility, recipients=None, send_email=None, message=None,
             copy_me=None, notify=None, link_to_current=None,
             expiry=None, add_filename=None):
        """
        Create a link to this file.
        """
        return links.Links(self._client.create_link(path=self.path, kind=Const.LINK_KIND_FILE, accessibility=accessibility,
            recipients=recipients, send_email=send_email, message=message,
            copy_me=copy_me, notify=notify, link_to_current=link_to_current,
            expiry=expiry, add_filename=add_filename))

class Files(HasClient):
    """
    Collection of files.
    """

class Folder(Item):
    """
    Wrapper for a folder the cloud.
    Does not have to exist - can represent a new folder yet to be created.
    """
    def folder(self, path):
        """Return a subfolder of this folder."""
        return Folder(self._client, path=self.path + '/' + path)

    def file(self, filename):
        """Return a file in this folder."""
        return File(self._client, folder=self, filename=filename, path=self.path + '/' + filename)

    def save(self):
        """Save changed properties of an existing folder."""

    def create(self, ignore_if_exists=True):
        """
        Create a new folder in the Egnyte cloud.
        If ignore_if_exists is True, error raised if folder already exists will be ignored.
        """
        return self._client.create_folder(self.path, ignore_if_exists)

    def delete(self):
        """Delete this folder in the cloud."""
        self._client.delete_folder(self.path)

    def copy(self, destination):
        """Copy this folder to another path. Destination path should include all segments."""
        self._client.copy(self.path, destination)
        return self._client.folder(destination)

    def move(self, destination):
        """Move this folder to another path. Destination path should include all segments."""
        self._client.move(self.path, destination)
        return self._client.folder(destination)

    def link(self, accessibility, recipients=None, send_email=None, message=None,
             copy_me=None, notify=None, link_to_current=None,
             expiry=None, add_filename=None):
        """
        Create a link to this folder.
        """
        return links.Links(self._client.link_create(path=self.path, kind=Const.LINK_KIND_PATH, accessibility=accessibility,
            recipients=recipients, send_email=send_email, message=message,
            copy_me=copy_me, notify=notify, link_to_current=link_to_current,
            expiry=expiry, add_filename=add_filename))


class Folders(HasClient):
    """Collection of folders"""

    

class FileDownload(object):
    """
    Provides file length and other metadata.
    Delegates reads to underlying requests response.
    """

    def __init__(self, response):
        self.response = response

    def __len__(self):
        return int(self.response.headers['content-length'])

    def write_to(self, fp):
        """Copy data to a file, then close the source."""
        with closing(self):
            for chunk in self.iter_content():
                fp.write(chunk)

    def close(self):
        self.response.close()

    def closed(self):
        return self.response.closed()

    def read(self, amt=None, decode_content=True):
        """
        Wrap urllib3 response.
        amt - How much of the content to read. If specified, caching is skipped because it doesn't make sense to cache partial content as the full response.
        decode_content - If True, will attempt to decode the body based on the 'content-encoding' header.
        """
        return self.response.raw.read(amt, decode_content)

    def __iter__(self, **kwargs):
        """
        Iterate resposne body line by line.
        You can speficify alternate delimiter with delimiter parameter.
        """
        return self.response.iter_lines(**kwargs)

    def iter_content(self, chunk_size = 16 * 1024):
        return self.response.iter_content(chunk_size)

