import datetime

from egnyte.exc import default, created, InvalidParameters
from egnyte import base, files, users


class Const:
    LINK_KIND_FILE = "file"
    LINK_KIND_FOLDER = "folder"
    LINK_KIND_LIST = (LINK_KIND_FILE, LINK_KIND_FOLDER)

    LINK_ACCESSIBILITY_ANYONE = "anyone"  # accessible by anyone with link
    LINK_ACCESSIBILITY_PASSWORD = "password"  # accessible by anyone with link
    # who knows password
    LINK_ACCESSIBILITY_DOMAIN = "domain"  # accessible by any domain user
    # (login required)
    LINK_ACCESSIBILITY_RECIPIENTS = "recipients"  # accessible by link recipients,
    # who must be domain users
    # (login required)
    LINK_ACCESSIBILITY_LIST = (
        LINK_ACCESSIBILITY_ANYONE,
        LINK_ACCESSIBILITY_PASSWORD,
        LINK_ACCESSIBILITY_DOMAIN,
        LINK_ACCESSIBILITY_RECIPIENTS,
    )
    USER_INFO_URI = "pubapi/v1/userinfo"
    FOLDER_URI = "pubapi/v1/fs%(folderpath)s"
    FILE_URI = "pubapi/v1/fs-content/%(filepath)s"
    LINK_URI = "pubapi/v1/links"
    LINK_URI2 = "pubapi/v1/links/%(id)s"

    ACTION_ADD_FOLDER = 'add_folder'
    ACTION_MOVE = 'move'
    ACTION_COPY = 'copy'


class EgnyteClient(base.Session):

    # User API

    def user_info(self):
        return default.check_json_response(self.GET(self.get_url(Const.USER_INFO_URI)))

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

    def create_folder(self, folderpath):
        url = self.get_url(Const.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': Const.ACTION_ADD_FOLDER})
        created.check_response(r)

    def delete_folder(self, folderpath):
        url = self.get_url(Const.FOLDER_URI, folderpath=folderpath)
        r = self.DELETE(url)
        default.check_response(r)

    def get_file_contents(self, filepath):
        url = self.get_url(Const.FILE_URI, filepath=filepath)
        r = self.GET(url, stream=True)
        default.check_response(r)
        return files.FileDownload(r)

    def put_file_contents(self, filepath, fptr):
        url = self.get_url(Const.FILE_URI, filepath=filepath)
        r = self.POST(url, data=fptr)
        default.check_response(r)

    def move(self, folderpath, destination):
        url = self.get_url(Const.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': Const.ACTION_MOVE, 'destination': destination})
        default.check_response(r)

    def copy(self, folderpath, destination):
        url = self.get_url(Const.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': Const.ACTION_COPY, 'destination': destination})
        default.check_response(r)

    def list_content(self, folderpath):
        url = self.get_url(Const.FOLDER_URI, folderpath=folderpath)
        r = self.GET(url)
        return default.check_json_response(r)

    # Links API

    def create_link(self, path, kind, accessibility,
                    recipients=None, send_email=None, message=None,
                    copy_me=None, notify=None, link_to_current=None,
                    expiry=None, add_filename=None,
                    ):
        if kind not in Const.LINK_KIND_LIST:
            raise InvalidParameters('kind', kind)
        if accessibility not in Const.LINK_ACCESSIBILITY_LIST:
            raise InvalidParameters('accessibility', accessibility)
        url = self.get_url(Const.LINK_URI)
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
        if kind == Const.LINK_KIND_FILE and link_to_current is not None:
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
        url = self.get_url(Const.LINK_URI2, id=id)
        r = self.DELETE(url)
        default.check_response(r)

    def link_details(self, id):
        url = self.get_url(Const.LINK_URI2, id=id)
        r = self.GET(url)
        return default.check_json_response(r)

    def links(self):
        # TODO
        pass
