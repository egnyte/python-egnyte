from __future__ import unicode_literals

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
        """Copy this to another path. Destination path should have all segments (including the last one)."""
        return self._action('copy', destination)

    def move(self, destination):
        """Move this to another path. Destination path should have all segments (including the last one)."""
        return self._action('move', destination)

    def link(self, accessibility, recipients=None, send_email=None, message=None,
             copy_me=None, notify=None, link_to_current=None,
             expiry_date=None, expiry_clicks=None, add_filename=None):
        """
        Create a link.

        * accessibility: Determines how the link can be accessed ('Anyone', 'Password', 'Domain', 'Recipients')
        * send_email: If true, Egnyte will send the link by email.
        * recipients: List email addresses for people who should receive the link. Only required if send_email is True (List of valid email addresses)
        * message: Personal message to be sent in link email. Only applies if send_email is True (plain text)
        * copy_me: If True, a copy of the link message will be sent to the link creator. Only applies if send_email is True.
        * notify: If True, link creator will be notified via email when link is accessed.
        * link_to_current: If True, link will always refer to current version of file. Only applicable for file links.
        * expiry_date: The expiry date for the link. If expiry_date is specified, expiry_clicks cannot be set (future date as datetime.date or string in YYYY-MM-DD format)
        * expiry_clicks: The number of times the link can be clicked before it stops working. If expiry_clicks is specified, expiry_date cannot be set (value must be between 1 - 10, inclusive)
        * add_filename: If True then the filename will be appended to the end of the link. Only applies to file links, not folder links.

        Will return sequence of created Links, one for each recipient.
        """
        return Links(self._client).create(path=self.path, type=self._link_kind, accessibility=accessibility,
                                          recipients=recipients, send_email=send_email, message=message,
                                          copy_me=copy_me, notify=notify, link_to_current=link_to_current,
                                          expiry_date=expiry_date, expiry_clicks=expiry_clicks, add_filename=add_filename)

    def _get(self):
        """Get the right object type (File or Folder), depending on what this path points to in the Cloud File System"""
        json = exc.default.check_json_response(self._client.GET(self._url))
        if json['is_folder'] and not isinstance(self, Folder):
            instance = Folder(self._client, path=self.path)
        elif not json['is_folder'] and not isinstance(self, File):
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
    Does not have to exist - this can represent a new file to be uploaded.
    path - file path
    """
    _upload_chunk_size = 100 * (1024 * 1024)  # 100 MB
    _upload_retries = 3
    _link_kind = 'file'
    _lazy_attributes = {'num_versions', 'name', 'checksum', 'last_modified', 'entry_id',
                        'uploaded_by', 'size', 'is_folder'}
    _url_template_content = "pubapi/v1/fs-content%(path)s"
    _url_template_content_chunked = "pubapi/v1/fs-content-chunked%(path)s"

    def upload(self, fp, size=None, progress_callback=None):
        """
        Upload file contents.
        fp can be any file-like object, but if you don't specify it's size in advance it must support tell and seek methods.
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
        Optional range is 2 integer sequence (start offset, end offset) used to download only part of the file.
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

    def delete(self):
        """Delete this file."""
        base.Resource.delete(self)

    def add_note(self, message):
        """Add a note to this file. Returns the created Note object."""
        return self._client.notes.create(self.path, message)

    def get_notes(self, **kwargs):
        """Get notes attached to this file. Returns list of Note objects"""
        return self._client.notes.list(file=self.path, **kwargs)


class Folder(FileOrFolder):
    """
    Wrapper for a folder the cloud.
    Does not have to exist - can represent a new folder yet to be created.
    """
    _url_template = "pubapi/v1/fs%(path)s"
    _url_template_permissions = "pubapi/v1/perms/folder/%(path)s"
    _url_template_effective_permissions = "pubapi/v1/perms/user/%(username)s"
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
        base.Resource.delete(self)

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

    def set_permissions(self, permission, users=None, groups=None):
        """
        Set permission level for some users and/or groups for this folder.
        """
        url = self._client.get_url(self._url_template_permissions, path=self.path)
        data = base.filter_none_values(dict(permission=permission, users=users, groups=groups))
        exc.default.check_response(self._client.POST(url, data))

    def get_effective_permissions(self, username):
        """
        Get effective permissions (both direct, and granted by membership in groups) to this folder for a specific user.
        username: name of user (string)
        Returns one of 'Owner', 'Full', 'Editor', 'Viewer'
        """
        url = self._client.get_url(self._url_template_effective_permissions, username=username)
        params = dict(folder=self.path)
        r = exc.default.check_json_response(self._client.GET(url, params=params))
        return r['permission']

    def get_notes(self, **kwargs):
        """Get notes attached to any file in this folder."""
        return self._client.notes.list(folder=self.path, **kwargs)


class Link(base.Resource):
    """Link to a file or folder"""
    _url_template = "pubapi/v1/links/%(id)s"
    _lazy_attributes = {'copy_me', 'link_to_current', 'accessibility', 'notify',
                        'path', 'creation_date', 'type', 'send_mail'}

    def delete(self):
        """Delete this link"""
        base.Resource.delete(self)


class User(base.Resource):
    """
    Wrapper for a User.
    Warning: attribute names in this class use camelCase instead of underscores.
    Name is a dictionary with 2 keys: givenName and lastName.
    """
    _url_template = "pubapi/v2/users/%(id)s"
    _url_template_effective_permissions = "pubabi/v1/perms/user/%(userName)s"
    _lazy_attributes = {'userName', 'externalId', 'email', 'name', 'active', 'locked', 'authType',
                        'role', 'userType', 'idpUserId'}

    def delete(self):
        """Delete this user account."""
        base.Resource.delete(self)

    def update(self, email=None, familyName=None, givenName=None, active=None, sendInvite=None, authType=None,
               userType=None, idpUserId=None, userPrincipalName=None):
        """
        Modify this user account.
        Optional parameters (no change if value is None):

        * email: The email address of the user. Any valid email address (e.g. admin@acme.com)
        * familyName: The last name of the user. Any plain text (e.g. John)
        * givenName: The first name of the user. Any plain text (e.g. Smith)
        * active: Whether the user is active or inactive. True or False
        * sendInvite: If set to true when creating a user, an invitation email will be sent (if the user is created in active state). True or False
        * authType: The authentication type for the user. 'ad' (AD), 'sso' (SAML SSO), 'egnyte' (Internal Egnyte)
        * userType: The Egnyte role of the user. 'admin' (Administrator), 'power' (Power User), 'standard' (Standard User)
        * idpUserId: Only required if the user is SSO authenticated and not using default user mapping. Do not specify if user is not SSO authenticated. This is the way the user is identified within the SAML Response from an SSO Identity Provider, i.e. the SAML Subject (e.g. jsmith)
        * userPrincipalName: Do not specify if user is not AD authenticated. Used to bind child authentication policies to a user when using Active Directory authentication in a multi-domain setup (e.g. jmiller@example.com)
        """
        url = self._client.get_url(self._url_template, id=self.id)
        name = base.filter_none_values(dict(familyName=familyName, givenName=givenName)) or None
        data = base.filter_none_values(dict(email=email, active=active, name=name, sendInvite=sendInvite, authType=authType, idpUserId=idpUserId, userPrincipalName=userPrincipalName))
        json = exc.default.check_json_response(self._client.PATCH(url, data))
        self._update_attributes(json)

    def get_effective_permissions(self, path):
        url = self._client.get_url(self._url_template_effective_permissions, userName=self.userName)
        r = exc.default.check_json_response(self._client.GET(url, params=dict(folder=path)))
        return r


class Note(base.Resource):
    """Note attached to a file or folder."""
    _url_template = "pubapi/v1/notes/%(id)s"
    _lazy_attributes = {'file_id', 'file_path', 'can_delete', 'creation_time', 'message', 'username', 'formatted_name'}

    def delete(self):
        """Delete this Note"""
        base.Resource.delete(self)

    def get_file(self):
        """Get the file to which this note is attached."""
        return self._client.file(self.file_path)

class Group(base.Resource):
    """Group of users."""
    _url_template = "pubapi/v2/groups/%(id)s"
    _lazy_attributes = {'displayName', 'members'}

    def delete(self):
        """Delete this Group"""
        base.Resource.delete(self)


class Links(base.HasClient):
    """Link management API"""
    _url_template = "pubapi/v1/links"

    def create(self, path, type, accessibility,
               recipients=None, send_email=None, message=None,
               copy_me=None, notify=None, link_to_current=None,
               expiry_date=None, expiry_clicks=None, add_filename=None,
               ):
        """
        Create links.

        * path:  The absolute path of the destination file or folder.
        * type:  This determines what type of link will be created ('File' or 'Folder')
        * accessibility: Determines who a link is accessible by ('Anyone', 'Password', 'Domain', 'Recipients')
        * send_email: If True, the link will be sent via email by Egnyte.
        * recipients: List email addresses of recipients of the link. Only required if send_email is True (List of valid email addresses)
        * message: Personal message to be sent in link email. Only applies if send_email is True (plain text)
        * copy_me: If True, a copy of the link message will be sent to the link creator. Only applies if send_email is True.
        * notify: If True, link creator will be notified via email when link is accessed.
        * link_to_current: If True, link will always refer to current version of file. Only applicable for file links.
        * expiry_date: The expiry date for the link. If expiry_date is specified, expiry_clicks cannot be set (future date as datetime.date or string in YYYY-MM-DD format)
        * expiry_clicks: The number of clicks the link is valid for. If expiry_clicks is specified, expiry_date cannot be set (value must be between 1 - 10, inclusive)
        * add_filename: If True then the filename will be appended to the end of the link. Only applies to file links, not folder links.

        Will return a sequence of created Links, one for each recipient.
        """
        url = self._client.get_url(self._url_template)
        data = base.filter_none_values(dict(path=path, type=type, accessibility=accessibility, send_email=send_email,
                                            copy_me=copy_me, notify=notify, add_filename=add_filename, link_to_current=link_to_current,
                                            expiry_clicks=expiry_clicks, expiry_date=base.date_format(expiry_date),
                                            recipients=recipients, message=message))
        response = exc.default.check_json_response(self._client.POST(url, data))
        # This response has weird structure
        links = response.pop('links')
        result = []
        for l in links:
            l.update(response)
            result.append(Link(self._client, **l))
        return result

    def get(self, id):
        """Get a Link object by it's id"""
        return Link(self._client, id=id)

    def list(self, path=None, username=None, created_before=None, created_after=None, type=None, accessibility=None,
             offset=None, count=None):
        """
        Search links that match following optional conditions:

        * path: List links to this file or folder (Full absolute path of destination file or folder)
        * username: List links created by this user (Any username from your Egnyte account)
        * created_before: List links created before this date (datetime.date, or string in YYYY-MM-DD format)
        * created_after: List links created after this date (datetime.date, or string in YYYY-MM-DD format)
        * type: Links of selected type will be shown ('File' or 'Folder')
        * accessibility: Links of selected accessibility will be shown ('Anyone', 'Password', 'Domain', or 'Recipients')
        * offset: Start at this link, where offset=0 means start with first link.
        * count: Send this number of links. If not specified, all links will be sent.

        Returns a list of Link objects, with additional total_count and offset attributes.
        """
        url = self._client.get_url(self._url_template)
        params = base.filter_none_values(dict(path=path, username=username, created_before=base.date_format(created_before),
                                              created_after=base.date_format(created_after), type=type, accessibility=accessibility,
                                              offset=offset, count=count))
        json = exc.default.check_json_response(self._client.GET(url, params=params))
        return base.ResultList((Link(self._client, id=id) for id in json.get('ids', ())), json['total_count'], json['offset'])


class Users(base.HasClient):
    """User management API"""
    _url_template = "pubapi/v2/users"

    def list(self, email=None, externalId=None, userName=None, startIndex=None, count=None):
        """
        Search users. Optional search parameters are 'email', 'externalId' and 'userName'.
        startIndex (starts with 1) and count may be used for pagination

        Returns a list of User objects, with additional total_count and offset attributes.
        """
        url = self._client.get_url(self._url_template)
        filters = base.filter_none_values(dict(email=email, externalId=externalId, userName=userName))
        params = base.filter_none_values(dict(startIndex=startIndex, count=count))
        params['filter'] = [u'%s eq "%s"' % (k, v) for (k, v) in filters.items()]
        json = exc.default.check_json_response(self._client.GET(url, params=params))
        return base.ResultList((User(self._client, **d) for d in json.get('resources', ())), json['totalResults'], json['startIndex'] - 1)

    def get(self, id):
        """Get a User object by id. Does not check if User exists."""
        return User(self._client, id=id)

    def by_email(self, email):
        """Get a User object by email. Returns None if user does not exist"""
        try:
            return self.list(email=email)[0]
        except LookupError:
            pass

    def by_username(self, userName):
        """Get a User object by username. Returns None if user does not exist"""
        try:
            return self.list(userName=userName)[0]
        except LookupError:
            pass

    def create(self, userName, externalId, email, familyName, givenName, active=True, sendInvite=True, authType='egnyte',
               userType='power', role=None, idpUserId=None, userPrincipalName=None):
        """
        Create a new user account. Parameters:

        * userName: The Egnyte username for the user. Username must start with a letter or digit. Special characters are not supported (with the exception of periods, hyphens, and underscores).
        * externalId: This is an immutable unique identifier provided by the API consumer. Any plain text (e.g. S-1-5-21-3623811015-3361044348-30300820-1013)
        * email: The email address of the user. Any valid email address (e.g. admin@acme.com)
        * familyName: The last name of the user. Any plain text (e.g. John)
        * givenName: The first name of the user. Any plain text (e.g. Smith)
        * active: Whether the user is active or inactive. True or False
        * sendInvite: If set to true when creating a user, an invitation email will be sent (if the user is created in active state). True or False
        * authType: The authentication type for the user. 'ad' (AD), 'sso' (SAML SSO), 'egnyte' (Internal Egnyte)
        * userType: The type of the user. 'admin' (Administrator), 'power' (Power User), 'standard' (Standard User)
        * role: The role assigned to the user. Only applicable for Power Users. Default or custom role name
        * idpUserId: Only required if the user is SSO authenticated and not using default user mapping. Do not specify if user is not SSO authenticated. This is the way the user is identified within the SAML Response from an SSO Identity Provider, i.e. the SAML Subject (e.g. jsmith)
        * userPrincipalName: Do not specify if user is not AD authenticated. Used to bind child authentication policies to a user when using Active Directory authentication in a multi-domain setup (e.g. jmiller@example.com)

        Returns created User object.
        """
        url = self._client.get_url(self._url_template)
        data = base.filter_none_values(dict(userName=userName, externalId=externalId, email=email,
                                            name=dict(familyName=familyName, givenName=givenName), active=active, sendInvite=sendInvite, authType=authType,
                                            userType=userType, role=role, idpUserId=idpUserId, userPrincipalName=userPrincipalName))
        json = exc.created.check_json_response(self._client.POST(url, data))
        return User(self._client, **json)


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


class Notes(base.HasClient):
    """
    Notes management API
    """
    _url_template = "pubapi/v1/notes"

    def create(self, path, message):
        """
        Create a new note.
        Parameters:

        * path - path to the file the note is about
        * message - contents of the note

        Returns the created Note object.
        """
        url = self._client.get_url(self._url_template)
        data = dict(path=path, body=message)
        json = exc.created.check_json_response(self._client.POST(url, data))
        return Note(self._client, **json)

    def list(self, file=None, folder=None, start_time=None, end_time=None):
        """
        List existing notes.
        Optional filtering parameters:

        * start_time: Get notes created after start_time (datetime.date or string in 'YYYY-MM-DD' format)
        * file: Get only notes attached to a specific file (path).
        * folder: Get only notes atatched to files in specific folder (path).
        * end_time: Get notes created before end_time (datetime.date or string in 'YYYY-MM-DD' format)

        Returns list of Note objects, with additional attributes total_count and offset.
        """
        url = self._client.get_url(self._url_template)
        params = base.filter_none_values(dict(file=file, folder=folder, start_time=base.date_format(start_time),
                                              end_time=base.date_format(end_time)))
        json = exc.default.check_json_response(self._client.GET(url, params=params))
        return base.ResultList((Note(self._client, **d) for d in json.pop('notes', ())), json['total_results'], json['offset'])


class Groups(base.HasClient):
    """
    Group Management API
    """
    _url_template = "pubapi/v2/groups"

    def list(self, displayName=None, startIndex=None, count=None):
        """
        List existing groups.
        Optional filtering parameters:
        
        * displayName: Filter by name of the group. This may contain '*' wildcards at beginning for prefix search or both at beginning and end for contains search.

        Returns list of Group objects, with additional attributes total_result and offset
        """
        params = base.filter_none_values(dict(startIndex=startIndex, count=count))
        if displayName:
            if displayName.startswith('*'):
                op = 'co' if displayName.endswith('*') else 'sw'
            else:
                op = 'eq'
            params['filter'] = [u'displayName %s "%s"' % (op, displayName.strip('*'))]
        url = self._client.get_url(self._url_template)
        json = exc.default.check_json_response(self._client.GET(url, params=params))
        return base.ResultList((Group(self._client, **d) for d in json.pop('resources', ())), json['totalResults'], json['startIndex'] - 1)

    def create(self, displayName, members=None):
        """
        Create a new Group. Parameters:

        * displayName: Name of the group (string). Required
        * members: List of members to be added to the new group (user ids or User objects). Optional.

        Returns created Group object.
        """
        url = self._client.get_url(self._url_template)
        data = dict(displayName=displayName)
        if members is not None:
            data['members'] = [dict(value=x.id if isinstance(x, User) else x) for x in members]
        json = exc.created.check_json_response(self._client.POST(url, data))
        return Group(self._client, **json)

    def get(self, id):
        """Get a Group object by id. Does not check if Group exists."""
        return Group(self._client, id=id)

    def by_displayName(self, displayName):
        """Get a Group object by displayName. Returns None if Group does not exist"""
        try:
            return self.list(displayName=displayName)[0]
        except LookupError:
            pass

class SearchMatch(base.HasClient):
    """
    Single match from search results.
    Attributes for a file match:
    
    * name The name of the file.
    * path The path to the file in Egnyte.
    * type The MIME type of the file.
    * size The size of the file in bytes.
    * snippet A plain text snippet of the text containing the matched content.
    * snippet_html An HTML formatted snippet of the text containing the matched content.
    * entry_id A GUID for tha particular instance of a file.
    * last_modified The ISO-8601 formatted timestamp representing the last modified date of the file.
    * uploaded_by The formatted name of the user who uploaded the file.
    * uploaded_by_username The username of the user who uploaded the file.
    * num_versions The number of versions of the file available.
    * is_folder A boolean value stating if the object is a file or folder. Please note that, currently, this API only returns file objects.
    """

    def file(self):
        """Get File object that correspons to this search match, or None if found resource is not a File"""
        if not self.is_folder:
            return File(self._client, name=self.name, path=self.path, is_folder=self.is_folder, num_versions=self.num_versions,
                        entry_id=self.entry_id, uploaded_by=self.uploaded_by, size=self.size, last_modified=self.last_modified)


class Search(base.HasClient):
    """Search API"""
    _url_template = "pubapi/v1/search"

    def files(self, query, offset=None, count=None, folder=None, modified_after=None, modified_before=None):
        """
        Search for files.
        Parameters:

        * query The search string you want to find. * is supported as a postfix wildcard, AND and OR as bool operations and double quotes for phrase search.
        * offset The 0-based index of the initial record being requested (Integer >= 0).
        * count The number of entries per page (min 1, max 100)
        * folder Limit the result set to only items contained in the specified folder.
        * modified_before Limit to results before the specified ISO-8601 timestamp (datetime.date object or string).
        * modified_after Limit to results after the specified ISO-8601 timestamp (datetime.date object or string).

        Returns list of SearchMatch objects, with additional attributes total_count and offset.
        """
        url = self._client.get_url(self._url_template)
        params = base.filter_none_values(dict(
            query=query,
            offset=offset,
            count=count,
            folder=folder,
            modified_after=base.date_format(modified_after),
            modified_before=base.date_format(modified_before))
        )
        json = exc.default.check_json_response(self._client.GET(url, params=params))
        return base.ResultList((SearchMatch(self._client, **d) for d in json.get('results', ())), json['total_count'], json['offset'])
