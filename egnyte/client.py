from __future__ import print_function

import datetime

import six

from egnyte.exc import default, created, created_ignore_existing, InvalidParameters, ChecksumError
from egnyte import base, files, users, links


class EgnyteClient(base.Session):
    upload_chunk_size = 10 * (1024 * 1024) # 10 MB
    upload_chunk_retries = 3

    # User API

    def user_info(self):
        return default.check_json_response(self.GET(self.get_url(base.Const.USER_INFO_URI)))

    def users(self):
        return users.Users(self)

    def users_where(self, where):
        return users.Users(self, where=where)

    def users_search(self, search_string):
        return users.Users(self, search_string=search_string)

    def user_by_id(self, id):
        return users.User(self, id=id)

    def user_by_email(self, email):
        return users.User(self, email=email)

    def create_user(self, **kwargs):
        return users.User(self, **kwargs)

    def delete_user(self, id):
        pass

    # Folder and file operations

    def folder(self, path="/Shared"):
        return files.Folder(self, path=path)

    def file(self, path):
        return files.File(self, path=path)

    def create_folder(self, folderpath, ignore_if_exists=True):
        url = self.get_url(base.Const.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': base.Const.ACTION_ADD_FOLDER})
        (created_ignore_existing if ignore_if_exists else created).check_response(r)

    def delete_folder(self, folderpath):
        url = self.get_url(base.Const.FOLDER_URI, folderpath=folderpath)
        r = self.DELETE(url)
        default.check_response(r)

    def get_file_contents(self, filepath):
        url = self.get_url(base.Const.FILE_URI, filepath=filepath)
        r = self.GET(url, stream=True)
        default.check_response(r)
        return files.FileDownload(r)

    def put_file_contents(self, filepath, fp, size=None):
        """
        Upload a file to cloud.
        fp can be bytes or any file-like object, but if you don't specify it's size in
        advance it must support tell and seek methods.
        """
        url = self.get_url(base.Const.FILE_URI, filepath=filepath)
        if isinstance(fp, six.binary_type):
            fp = six.BytesIO(fp)
        if size is None:
            size = base.get_file_size(fp)
        if size < self.upload_chunk_size:
            # simple, one request upload
            chunk = base._FileChunk(fp, 0, size)
            r = self.POST(url, data=chunk, headers={'Content-length': size})
            default.check_response(r)
            server_sha = r.headers['X-Sha512-Checksum']
            our_sha = chunk.sha.hexdigest()
            if server_sha != our_sha:
                raise ChecksumError("Failed to upload file", {})
        else: # chunked upload
            return self._chunked_upload(filepath, fp, size)

    def _chunked_upload(self, filepath, fp, size):
        url = self.get_url(base.Const.FILE_URI_CHUNKED, filepath=filepath)
        chunks = list(base.split_file_into_chunks(fp, size, self.upload_chunk_size)) # need count of chunks
        chunk_count = len(chunks)
        headers = {}
        for chunk_number, chunk in enumerate(chunks, 1):  # count from 1 not 0
            headers['x-egnyte-chunk-num'] = "%d" % chunk_number
            headers['content-length'] = chunk.size
            if chunk_number == chunk_count: # last chunk
                headers['x-egnyte-last-chunk'] = "true"
            retries = max(self.upload_chunk_retries, 1)
            while retries > 0:
                r = self.POST(url, data=chunk, headers=headers)
                server_sha = r.headers['x-egnyte-chunk-sha512-checksum']
                our_sha = chunk.sha.hexdigest()
                if server_sha == our_sha:
                    break
                retries -= 1
            if retries == 0:
                raise ChecksumError("Failed to upload file chunk", {"chunk_number": chunk_number, "start_position": chunk.position})
            default.check_response(r)
            if chunk_number == 1:
                headers['x-egnyte-upload-id'] = r.headers['x-egnyte-upload-id']

    def move(self, folderpath, destination):
        url = self.get_url(base.Const.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': base.Const.ACTION_MOVE, 'destination': destination})
        default.check_response(r)

    def copy(self, folderpath, destination):
        url = self.get_url(base.Const.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': base.Const.ACTION_COPY, 'destination': destination})
        default.check_response(r)

    def list_content(self, folderpath):
        url = self.get_url(base.Const.FOLDER_URI, folderpath=folderpath)
        r = self.GET(url)
        return default.check_json_response(r)

    # Links API

    def link_create(self, path, kind, accessibility,
                    recipients=None, send_email=None, message=None,
                    copy_me=None, notify=None, link_to_current=None,
                    expiry=None, add_filename=None,
                    ):
        if kind not in base.Const.LINK_KIND_LIST:
            raise InvalidParameters('kind', kind)
        if accessibility not in base.Const.LINK_ACCESSIBILITY_LIST:
            raise InvalidParameters('accessibility', accessibility)
        url = self.get_url(base.Const.LINK_URI)
        data = {
            "path": path,
            "type": kind,
            "accessibility": accessibility,
        }
        if send_email is not None:
            data['sendEmail'] = send_email
        if copy_me is not None:
            data['copyMe'] = copy_me
        if notify is not None:
            data['notify'] = notify
        if add_filename is not None:
            data['addFilename'] = add_filename
        if kind == base.Const.LINK_KIND_FILE and link_to_current is not None:
            data["linkToCurrent"] = link_to_current
        if recipients:
            data['recipients'] = recipients
        if expiry is not None:
            if isinstance(expiry, int):
                data["expiryClicks"] = expiry
            elif type(expiry) == datetime.date:
                data["expiryDate"] = expiry.strftime("%Y-%m-%d")
        if message is not None:
            data['message'] = message
        r = self.POST(url, data)
        return default.check_json_response(r)

    def link_delete(self, id):
        url = self.get_url(base.Const.LINK_URI2, id=id)
        r = self.DELETE(url)
        default.check_response(r)

    def link_details(self, id):
        url = self.get_url(base.Const.LINK_URI2, id=id)
        r = self.GET(url)
        return default.check_json_response(r)

    def links(self):
        # TODO
        pass

