from __future__ import print_function

from egnyte import exc, base, resources, audits

class EgnyteClient(base.Session):
    """Main client objects. This should be the only object you have to manually create in standard API use."""

    @property
    def links(self):
        """API for Links management"""
        return resources.Links(self)

    @property
    def user_info(self):
        return exc.default.check_json_response(self.GET(self.get_url("pubapi/v1/userinfo")))

    @property
    def users(self):
        """API for User management"""
        return resources.Users(self)

    @property
    def audits(self):
        return audits.Audits(self)

    def folder(self, path="/Shared"):
        """Get a Folder object for the specified path"""
        return resources.Folder(self, path=path)

    def file(self, path):
        """Get a File object for the specified path"""
        return resources.File(self, path=path)
