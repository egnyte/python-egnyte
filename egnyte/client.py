from __future__ import print_function

from egnyte import exc, base, resources, const

class EgnyteClient(base.Session):
    """Main client objects. This should be the only object you have to manually create in standard API use."""

    def user_info(self):
        return exc.default.check_json_response(self.GET(self.get_url("pubapi/v1/userinfo")))

    def users(self):
        """API for User management"""
        return resources.Users(self)

    def folder(self, path="/Shared"):
        """Get a Folder object for the specified path"""
        return resources.Folder(self, path=path)

    def file(self, path):
        """Get a File object for the specified path"""
        return resources.File(self, path=path)

    def links(self):
        """API for Links management"""
        return resources.Links(self)
