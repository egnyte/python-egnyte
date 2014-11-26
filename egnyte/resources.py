import collections

import six

from egnyte import base, exc


class FileOrFolder(base.Resource):
    """Things that are common to both files and folders."""
    _url_template = "pubapi/v1/fs%(path)s"
    _lazy_attributes = {'name', 'folder_id', 'is_folder'}

    def _action(self, action, destination):
        exc.default.check_response(self._client.POST(self._url, dict(action=action, destination=destination)))
        return self.__class__(self._client, path=destination)

    def copy(self, destination):
        """Copy this to another path. Destination path should have all segments (including last one)."""
        return self._action('copy', destination)

    def move(self, destination):
        """Move this to another path. Destination path should have all segments (including last one)."""
        return self._action('move', destination)

    def link(self, accessibility, recipients=None, send_email=None, message=None,
             copy_me=None, notify=None, link_to_current=None,
             expiry_date=None, expiry_clicks=None, add_filename=None):
        """
        Create a link to this.
        accessibility: Determines who a link is accessible by ('Anyone', 'Password', 'Domain', 'Recipients')
        send_email: If true, link will be sent via email by Egnyte.
        recipients: List email addresses of recipients of the link. Only required if send_email is True (List of valid email addresses)
        message: Personal message to be sent in link email. Only applies if send_email is True (plain text)
        copy_me: If True, a copy of the link message will be sent to the link creator. Only applies if send_email is True.
        notify: If True, link creator will be notified via email when link is accessed.
        link_to_current: If True, link will always refer to current version of file. Only applicable for file links.
        expiry_date: The expiry date for the link. If expiry_date is specified, expiry_clicks cannot be set (future date as datetime.date or string in YYYY-MM-DD format)
        expiry_clicks: The number of clicks the link is valid for. If expiry_clicks is specified, expiry_date cannot be set (value must be between 1 - 10, inclusive)
        add_filename: If True then the filename will be appended to the end of the link. Only applies to file links, not folder links.

        Will return sequence of created Links, one for each recipient.
        """
        return Links(self._client).create(path=self.path, type=self._link_kind, accessibility=accessibility,
                                          recipients=recipients, send_email=send_email, message=message,
                                          copy_me=copy_me, notify=notify, link_to_current=link_to_current,
                                          expiry_date=expiry_date, expiry_clicks=expiry_clicks, add_filename=add_filename)

    def _get(self):
        """Get the appropiate object type (File or Folder), depending on what this path points to in the Cloud File System"""
        json = exc.default.check_json_response(self._client.GET(self._url))
        if json['is_folder'] and not isinstance(self, Folder):
            instance = Folder(self._client, path=self.path)
        elif not json['is_folder'] and not instance(self, File):
            instance = File(self._client, path=self.path)
        else:
            instance = self
        instance._update_attributes(json)
        if instance.is_folder:
            instance.folders = [Folder(self._client, **folder_data) for folder_data in json.get('folders', ())]
            instance.files = [File(self._client, **file_data) for file_data in json.get('files', ())]
        return instance

        


class File(FileOrFolder):
    """
    Wrapper for a file in the cloud.
    Does not have to exist - can represent a new file to be uploaded.
    path - file path
    """
    _upload_chunk_size = 100 * (1024 * 1024)  # 100 MB
    _upload_retries = 3
    _link_kind = 'file'
    _lazy_attributes = {'num_versions', 'name', 'checksum', 'last_modified', 'entry_id',
                        'uploaded_by', 'size', 'is_folder'}
    _url_template_content = "pubapi/v1/fs-content%(path)s"
    _url_template_content_chunked = "pubapi/v1/fs-content-chunked%(filepath)s"

    def upload(self, fp, size=None, progress_callback=None):
        """
        Upload file contents.
        fp can be any file-like object, but if you don't specify it's size in
        advance it must support tell and seek methods.
        Progress callback is optional - if provided, it should match signature of ProgressCallbacks.upload_progress
        """
        if isinstance(fp, six.binary_type):
            fp = six.BytesIO(fp)
        if size is None:
            size = base.get_file_size(fp)
        if size < self._upload_chunk_size:
            # simple, one request upload
            retries = max(self._upload_retries, 1)
            while retries > 0:
                url = self._client.get_url(self._url_template_content, path=self.path)
                chunk = base._FileChunk(fp, 0, size)
                r = self._client.POST(url, data=chunk, headers={'Content-length': size})
                exc.default.check_response(r)
                server_sha = r.headers['X-Sha512-Checksum']
                our_sha = chunk.sha.hexdigest()
                if server_sha == our_sha:
                    break
                retries -= 1
                # TODO: retry network errors too
            if retries == 0:
                raise exc.ChecksumError("Failed to upload file", {})
        else:  # chunked upload
            return self._chunked_upload(fp, size, progress_callback)

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
            r = exc.partial.check_response(self._client.GET(url, stream=True, headers={'Range': 'bytes=%d-%d' % download_range}))
        return base.FileDownload(r, self)

    def _chunked_upload(self, fp, size, progress_callback):
        url = self._client.get_url(self._url_template_content_chunked, path=self.path)
        chunks = list(base.split_file_into_chunks(fp, size, self._upload_chunk_size))  # need count of chunks
        chunk_count = len(chunks)
        headers = {}
        for chunk_number, chunk in enumerate(chunks, 1):  # count from 1 not 0
            headers['x-egnyte-chunk-num'] = "%d" % chunk_number
            headers['content-length'] = chunk.size
            if chunk_number == chunk_count:  # last chunk
                headers['x-egnyte-last-chunk'] = "true"
            retries = max(self._upload_retries, 1)
            while retries > 0:
                r = self._client.POST(url, data=chunk, headers=headers)
                server_sha = r.headers['x-egnyte-chunk-sha512-checksum']
                our_sha = chunk.sha.hexdigest()
                if server_sha == our_sha:
                    break
                retries -= 1
                # TODO: retry network errors too
                # TODO: refactor common parts of chunked and standard upload
            if retries == 0:
                raise exc.ChecksumError("Failed to upload file chunk", {"chunk_number": chunk_number, "start_position": chunk.position})
            exc.default.check_response(r)
            if chunk_number == 1:
                headers['x-egnyte-upload-id'] = r.headers['x-egnyte-upload-id']
            if progress_callback is not None:
                progress_callback(self, size, chunk_number * self._upload_chunk_size)

class Folder(FileOrFolder):
    """
    Wrapper for a folder the cloud.
    Does not have to exist - can represent a new folder yet to be created.
    """
    _url_template = "pubapi/v1/fs%(path)s"
    _url_template_permissions = "pubapi/v1/perms/folder/%(path)s"
    _url_template_effective_permissions = "pubabi/v1/perms/user/%(username)s"
    _lazy_attributes = {'name', 'folder_id', 'is_folder'}
    _link_kind = 'folder'
    folders = None
    files = None

    def folder(self, path, **kwargs):
        """Return a subfolder of this folder."""
        return Folder(self._client, path=self.path + '/' + path, **kwargs)

    def file(self, filename, **kwargs):
        """Return a file in this folder."""
        return File(self._client, folder=self, filename=filename, path=self.path + '/' + filename, **kwargs)

    def create(self, ignore_if_exists=True):
        """
        Create a new folder in the Egnyte cloud.
        If ignore_if_exists is True, error raised if folder already exists will be ignored.
        """
        r = self._client.POST(self._url, dict(action='add_folder'))
        (exc.created_ignore_existing if ignore_if_exists else exc.created).check_response(r)
        return self

    def delete(self):
        """Delete this folder in the cloud."""
        r = self._client.DELETE(self._url)
        exc.default.check_response(r)

    def list(self):
        """
        Gets contents of this folder (in instance attributes 'folders' and 'files')
        """
        return self._get()

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
        return PermissionSet(r)

    def get_effective_permissions(self, username):
        url = self._client.get_url(self._url_template_effective_permissions, username=username)
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
    _url_template = "pubapi/v1/links"

    def create(self, path, type, accessibility,
               recipients=None, send_email=None, message=None,
               copy_me=None, notify=None, link_to_current=None,
               expiry_date=None, expiry_clicks=None, add_filename=None,
               ):
        """
        Create links.
        path:  The absolute path of the destination file or folder.
        type:  This determines what type of link will be created ('File' or 'Folder')
        accessibility: Determines who a link is accessible by ('Anyone', 'Password', 'Domain', 'Recipients')
        send_email: If true, link will be sent via email by Egnyte.
        recipients: List email addresses of recipients of the link. Only required if send_email is True (List of valid email addresses)
        message: Personal message to be sent in link email. Only applies if send_email is True (plain text)
        copy_me: If True, a copy of the link message will be sent to the link creator. Only applies if send_email is True.
        notify: If True, link creator will be notified via email when link is accessed.
        link_to_current: If True, link will always refer to current version of file. Only applicable for file links.
        expiry_date: The expiry date for the link. If expiry_date is specified, expiry_clicks cannot be set (future date as datetime.date or string in YYYY-MM-DD format)
        expiry_clicks: The number of clicks the link is valid for. If expiry_clicks is specified, expiry_date cannot be set (value must be between 1 - 10, inclusive)
        add_filename: If True then the filename will be appended to the end of the link. Only applies to file links, not folder links.

        Will return sequence of created Links, one for each recipient.
        """
        url = self._client.get_url(self._url_template)
        data = {k:v for (k, v) in dict(path=path, type=type, accessibility=accessibility, send_email=send_email,
                    copy_me=copy_me, notify=notify, add_filename=add_filename, link_to_current=link_to_current,
                    expiry_clicks=expiry_clicks, expiry_date=base.date_format(expiry_date),
                    recipients=recipients, message=message).items() if v is not None}
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

    def list(self, path=None, username=None, created_before=None, created_after=None, type=None, accessibility=None,
             offset=None, count=None):
        """
        Search links that match following optional conditions:
        path: List links to this file or folder (Full absolute path of destination file or folder)
        username: List links created by this user (Any username from your Egnyte account)
        created_before: List links created before this date (datetime.date, or string in YYYY-MM-DD format)
        created_after: List links created after this date (datetime.date, or string in YYYY-MM-DD format)
        type: Links of selected type will be shown ('File' or 'Folder')
        accessibility: Links of selected accessibility will be shown ('Anyone', 'Password', 'Domain', or 'Recipients')
        offset: Start at this link, where offset=0 means start with first link.
        count: Send this number of links. If not specified, all links will be sent.

        Returns sequence of Link objects.
        """
        url = self._client.get_url(self._url_template)
        params = {k:v for (k,v) in dict(path=path, username=username, created_before=base.date_format(created_before),
                    created_after=base.date_format(created_after), type=type, accessibility=accessibility,
                    offset=offset, count=count).items() if v is not None}
        r = exc.default.check_json_response(self._client.GET(url, params=params))
        return [self.get(id) for id in r['ids']]


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

class PermissionSet(object):
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


