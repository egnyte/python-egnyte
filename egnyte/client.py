import datetime

from egnyte.exc import default, created
from egnyte.base import Base

class Const:
    LINK_KIND_FILE = "file"
    LINK_KIND_FOLDER = "folder"
    LINK_KIND_LIST = [LINK_KIND_FILE, LINK_KIND_FOLDER, ]

    LINK_ACCESSIBILITY_ANYONE = "anyone"  # accessible by anyone with link
    LINK_ACCESSIBILITY_PASSWORD = "password"  # accessible by anyone with link
    # who knows password
    LINK_ACCESSIBILITY_DOMAIN = "domain"  # accessible by any domain user
    # (login required)
    LINK_ACCESSIBILITY_RECIPIENTS = "recipients"  # accessible by link recipients,
    # who must be domain users
    # (login required)
    LINK_ACCESSIBILITY_LIST = [
        LINK_ACCESSIBILITY_ANYONE,
        LINK_ACCESSIBILITY_PASSWORD,
        LINK_ACCESSIBILITY_DOMAIN,
        LINK_ACCESSIBILITY_RECIPIENTS,
    ]


class EgnyteClient(Base):
    USER_INFO_URI = r"pubapi/v1/userinfo"
    FOLDER_URI = r"pubapi/v1/fs%(folderpath)s"
    FILE_URI = r"pubapi/v1/fs-content/%(filepath)s"
    LINK_URI = r"pubapi/v1/links"
    LINK_URI2 = r"pubapi/v1/links/%(id)s"

    ACTION_ADD_FOLDER = 'add_folder'
    ACTION_MOVE = 'move'
    ACTION_COPY = 'copy'
    ITER_CHUNK_SIZE = 16 * 1024  # bytes

    def userinfo(self):
        return default.check_json_response(self.GET(self.get_url(self.USER_INFO_URI)))

    def create_folder(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=folderpath)
        r = self.POST(url, {'action': self.ACTION_ADD_FOLDER})
        created.check_response(r)

    def get_file(self, filepath):
        url = self.get_url(self.FILE_URI, filepath=filepath)
        r = self.GET(url, stream=True)
        default.check_response(r)
        for data in r.iter_content(self.ITER_CHUNK_SIZE):
            yield data

    def put_file(self, filepath, fptr):
        url = self.get_url(self.FILE_URI, filepath=filepath)
        r = self.POST(url, data=fptr, stream=True)
        default.check_response(r)

    def delete(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=folderpath)
        r = self.DELETE(url)
        default.check_response(r)

    def move(self, folderpath, destination):
        url = self.get_url(self.FOLDER_URI, folderpath=folderpath)
        data = {'action': self.ACTION_MOVE, 'destination': destination}
        r = self.POST(url, data)
        default.check_response(r)

    def copy(self, folderpath, destination):
        url = self.get_url(self.FOLDER_URI, folderpath=folderpath)
        data = {'action': self.ACTION_COPY, 'destination': destination}
        r = self.POST(url, data)
        default.check_response(r)

    def list_content(self, folderpath):
        url = self.get_url(self.FOLDER_URI, folderpath=folderpath)
        r = self.GET(url)
        return default.check_json_response(r)

    def create_link(self, path, kind, accessibility,
                    recipients=None, send_email=None, message=None,
                    copy_me=None, notify=None, link_to_current=None,
                    expiry=None, add_filename=None,
                    ):
        assert kind in Const.LINK_KIND_LIST
        assert accessibility in Const.LINK_ACCESSIBILITY_LIST
        if recipients is None:
            recipients = []
        url = self.get_url(self.LINK_URI)
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
            if type(expiry) == int:
                data["expiryClicks"] = expiry
            elif type(expiry) == datetime.date:
                data["expiryDate"] = expiry.strftime("%Y-%m-%d")
        if message is not None:
            data['message'] = message
        r = self.POST(url, data)
        return default.check_json_response(r)

    def link_delete(self, id):
        url = self.get_url(self.LINK_URI2, id=id)
        r = self.DELETE(url)
        default.check_response(r)

    def link_details(self, id):
        url = self.get_url(self.LINK_URI2, id=id)
        r = self.GET(url)
        return default.check_json_response(r)

    def links(self):
        # TODO
        pass
