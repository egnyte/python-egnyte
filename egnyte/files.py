from contextlib import closing

from egnyte.base import HasClient

class File(HasClient):

    def upload(self, fp):
        return self._client.put_file_contents(self.path)

    def download(self):
        return self._client.get_file_contents(self.path)

class Files(HasClient):
    pass

class Folder(HasClient):
    def folder(self, path):
        return Folder(self._client, path=self.path + '/' + path)


    def get_file(self, filename):
        return File(self._client, folder=self, filename=filename, path=self.path + '/' + filename)

    def save(self):
        pass

    def create(self):
        pass

class Folders(HasClient):
    pass

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

