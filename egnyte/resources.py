import collections
import datetime

import six

from egnyte import base, const, exc


class FileOrFolder(base.Resource):
    """Things that are common to both files and folders."""
    _url_template = "pubapi/v1/fs%(path)s"

    def _action(self, action, destination):
        exc.default.check_response(self._client.POST(self._url, dict(action=action, destination=destination)))
        return self.__class__(self._client, path=destination)

    def copy(self, destination):
        """Copy this to another path. Destination path should have all segments (including last one)."""
        return self._action(const.ACTION_COPY, destination)

    def move(self, destination):
        """Move this to another path. Destination path should have all segments (including last one)."""
        return self._action(const.ACTION_MOVE, destination)

    def link(self, accessibility, recipients=None, send_email=None, message=None,
             copy_me=None, notify=None, link_to_current=None,
             expiry=None, add_filename=None):
        """Create a link to this."""
        return Links(self._client).create(path=self.path, kind=self._link_kind, accessibility=accessibility,
                                          recipients=recipients, send_email=send_email, message=message,
                                          copy_me=copy_me, notify=notify, link_to_current=link_to_current,
                                          expiry=expiry, add_filename=add_filename)


class File(FileOrFolder):
    """
    Wrapper for a file in the cloud.
    Does not have to exist - can represent a new file to be uploaded.
    path - file path
    """
    _upload_chunk_size = 100 * (1024 * 1024)  # 10 MB
    _upload_chunk_retries = 3
    _link_kind = const.LINK_KIND_FILE
    _lazy_attributes = {'num_versions', 'name', 'checksum', 'last_modified', 'entry_id',
                        'uploaded_by', 'size', 'is_folder'}
    _url_template_content = "pubapi/v1/fs-content%(path)s"
    _url_template_content_chunked = "pubapi/v1/fs-content-chunked%(filepath)s"

    def upload(self, fp, size=None):
        """
        Upload file contents.
        fp can be any file-like object, but if you don't specify it's size in
        advance it must support tell and seek methods.
        """
        if isinstance(fp, six.binary_type):
            fp = six.BytesIO(fp)
        if size is None:
            size = base.get_file_size(fp)
        if size < self._upload_chunk_size:
            # simple, one request upload
            url = self._client.get_url(self._url_template_content, path=self.path)
            chunk = base._FileChunk(fp, 0, size)
            r = self._client.POST(url, data=chunk, headers={'Content-length': size})
            exc.default.check_response(r)
            server_sha = r.headers['X-Sha512-Checksum']
            our_sha = chunk.sha.hexdigest()
            if server_sha != our_sha:
                raise exc.ChecksumError("Failed to upload file", {})
        else:  # chunked upload
            return self._chunked_upload(fp, size)

    def download(self, download_range=None):
        """
        Download file contents.
        Returns a FileDownload.
        Optional range is 2 integer sequence (start offset, end offset) used to download
        only part of the file.
        """
        url = self._client.get_url(self._url_template_content, path=self.path)
        if download_range is None:
            r = exc.default.check_response(self._client.GET(url, stream=True))
        else:
            if len(download_range) != 2:
                raise exc.InvalidParameters('Download range needs to be None or a 2 element integer sequence')
            r = exc.partial.check_response(self._client.GET(url, stream=True,
                                                            headers={'Range': 'bytes=%d-%d' % download_range}))
        return base.FileDownload(r)

    def _chunked_upload(self, fp, size):
        url = self._client.get_url(self._url_template_content_chunked, path=self.path)
        chunks = list(base.split_file_into_chunks(fp, size, self._upload_chunk_size))  # need count of chunks
        chunk_count = len(chunks)
        headers = {}
        for chunk_number, chunk in enumerate(chunks, 1):  # count from 1 not 0
            headers['x-egnyte-chunk-num'] = "%d" % chunk_number
            headers['content-length'] = chunk.size
            if chunk_number == chunk_count:  # last chunk
                headers['x-egnyte-last-chunk'] = "true"
            retries = max(self._upload_chunk_retries, 1)
            while retries > 0:
                r = self._client.POST(url, data=chunk, headers=headers)
                server_sha = r.headers['x-egnyte-chunk-sha512-checksum']
                our_sha = chunk.sha.hexdigest()
                if server_sha == our_sha:
                    break
                retries -= 1
            if retries == 0:
                raise exc.ChecksumError("Failed to upload file chunk", {"chunk_number": chunk_number, "start_position": chunk.position})
            exc.default.check_response(r)
            if chunk_number == 1:
                headers['x-egnyte-upload-id'] = r.headers['x-egnyte-upload-id']

    def apply_changes(self):
        """Save changed properties of an existing folder."""
        raise NotImplementedError()


class Folder(FileOrFolder):
    """
    Wrapper for a folder the cloud.
    Does not have to exist - can represent a new folder yet to be created.
    """
    _url_template = "pubapi/v1/fs%(path)s"
    _url_template_permissions = "pubapi/v1/perms/folder/%(path)s"
    _url_template_effective_permissions = "pubabi/v1/perms/user/%(username)s"
    _lazy_attributes = {'name', 'folder_id', 'is_folder'}
    _link_kind = const.LINK_KIND_FOLDER

    def folder(self, path):
        """Return a subfolder of this folder."""
        return Folder(self._client, path=self.path + '/' + path)

    def file(self, filename):
        """Return a file in this folder."""
        return File(self._client, folder=self, filename=filename, path=self.path + '/' + filename)

    def apply_changes(self):
        """Save changed properties of an existing folder."""
        raise NotImplementedError()

    def create(self, ignore_if_exists=True):
        """
        Create a new folder in the Egnyte cloud.
        If ignore_if_exists is True, error raised if folder already exists will be ignored.
        """
        r = self._client.POST(self._url, dict(action=const.ACTION_ADD_FOLDER))
        (exc.created_ignore_existing if ignore_if_exists else exc.created).check_response(r)
        return self

    def delete(self):
        """Delete this folder in the cloud."""
        r = self._client.DELETE(self._url)
        exc.default.check_response(r)

    def list(self):
        """
        List contents of this folder.
        Returns dictionary with two keys, folders and files.
        Both are generators to list of Folder and Files contained here.
        """
        json = exc.default.check_json_response(self._client.GET(self._url))
        self._update_attributes(json)
        folders = (Folder(self._client, **folder_data) for folder_data in json.get('folders', ()))
        files = (File(self._client, **file_data) for file_data in json.get('files', ()))
        return {'folders': folders, 'files': files}

    def get_permissions(self, users=None, groups=None):
        """
        Get Permission values for this folder.
        """
        query_params = {}
        if users is not None:
            query_params[u'users'] = '|'.join(six.text_type(x) for x in users)
        if groups is not None:
            query_params[u'groups'] = '|'.join(six.text_type(x) for x in users)
        url = self._client.get_url(self._url_template_permissions, path=self.path)
        r = exc.default.check_json_response(self._client.GET(url, params=query_params))
        return Permissions(r)
        
    def get_effective_permissions(self, username):
        url = self._client.get_url(self._url_template_effective_permissions, username=username)
        print url
        r = exc.default.check_json_response(self._client.GET(url, params=dict(folder=self.path)))
        return r






class Link(base.Resource):
    """Link to a file or folder"""
    _url_template = "pubapi/v1/links/%(id)s"
    _lazy_attributes = {'copy_me', 'link_to_current', 'accessibility', 'notify',
                        'path', 'creation_date', 'type', 'send_mail'}

    def delete(self):
        exc.default.check_response(self._client.DELETE(self._url))


class User(base.Resource):
    _url_template_effective_permissions = "pubabi/v1/perms/user/%(username)s"

    def apply_changes(self):
        pass

    def create(self):
        pass

    def delete(self):
        pass

    def get_effective_permissions(self, path):
        url = self._client.get_url(self._url_template_effective_permissions, username=self.username)
        r = exc.default.check_json_response(self._client.GET(url, params=dict(folder=path)))
        return r



class Files(base.HasClient):
    """
    Collection of files.
    """


class Folders(base.HasClient):
    """Collection of folders"""


class Links(base.HasClient):
    """Collection of links"""

    def create(self, path, kind, accessibility,
               recipients=None, send_email=None, message=None,
               copy_me=None, notify=None, link_to_current=None,
               expiry=None, add_filename=None,
               ):
        """Creare links. Will return sequence of links of created, one for each recipient"""
        url = self._client.get_url("pubapi/v1/links")
        if kind not in const.LINK_KIND_LIST:
            raise exc.InvalidParameters('kind', kind)
        if accessibility not in const.LINK_ACCESSIBILITY_LIST:
            raise exc.InvalidParameters('accessibility', accessibility)
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
        if kind == const.LINK_KIND_FILE and link_to_current is not None:
            data["linkToCurrent"] = link_to_current
        if recipients:
            data['recipients'] = recipients
        if expiry is not None:
            if isinstance(expiry, int):
                data["expiryClicks"] = expiry
            elif type(expiry) == datetime.date:
                data["expiryDate"] = base.date_format(expiry)
        if message is not None:
            data['message'] = message
        response = exc.default.check_json_response(self._client.POST(url, data))
        # This response has weird structure
        links = response.pop('links')
        result = []
        for l in links:
            l.update(response)
            result.append(Link(self._client, **l))
        return result

    def get(self, id):
        return Link(self._client, id=id)


class Users(base.HasClient):
    """Collection of users"""

    def users_where(self, where):
        return Users(self._client, where=where)

    def users_search(self, search_string):
        return Users(self._client, search_string=search_string)

    def user_by_id(self, id):
        return User(self._client, id=id)

    def user_by_email(self, email):
        return User(self._client, email=email)

    # def create_user(self, **kwargs):
    #    return .User(self, **kwargs)

class Permissions(object):
    """Wrapper for a permission set"""
    def __init__(self, json):
        self._users = json.get('users', ())
        self._groups = json.get('groups', ())
        self._unpack()

    def _unpack(self):
        self.user_to_permission = {}
        self.group_to_permission = {}
        self.permission_to_owner = collections.defaultdict(lambda: dict(users=set(), groups=set()))
        for d in self._users:
            self.user_to_permission[d['subject']] = d['permission']
            self.permission_to_owner[d['permission']]['users'].add(d['subject'])
        for d in self._groups:
            self.group_to_permission[d['subject']] = d['permission']
            self.permission_to_owner[d['permission']]['groups'].add(d['subject'])

    

