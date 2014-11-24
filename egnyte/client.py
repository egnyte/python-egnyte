from __future__ import print_function

import os.path

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

    def folder(self, path="/Shared", **kwargs):
        """Get a Folder object for the specified path"""
        return resources.Folder(self, path=path.rstrip('/'), **kwargs)

    def file(self, path, **kwargs):
        """Get a File object for the specified path"""
        return resources.File(self, path=path, **kwargs)

    def get(self, path):
        """Check whether a path is a file or a folder and return appropiate object."""
        folder = self.folder(self, path=path).list()
        if folder.is_folder:
            return folder
        else:
            # a file after all
            return self.file(path=path, is_folder=False, name=folder.name)

    def bulk_upload(self, paths, target, exclude=None, progress_callbacks=None):
        """
        Transfer many files or directories to Cloud File System.
        paths - list of local file paths
        target - Path in CFS to upload to
        progress_callbacks - Callback object (see ProgressCallbacks)
        """
        if not paths: return
        if progress_callbacks is None:
            progress_callbacks = ProgressCallbacks() # no-op callbacks
        target_folder = self.folder(target)
        progress_callbacks.creating_directory(target_folder)
        target_folder.create(True)
        for is_dir, local_path, cloud_path in base.generate_paths(paths, exclude):
            if is_dir:
                cloud_dir = target_folder.folder(cloud_path)
                progress_callbacks.creating_directory(cloud_dir)
                cloud_dir.create(True)
            else:
                size = os.path.getsize(local_path)
                if size: # empty files cannot be uploaded
                    cloud_file = target_folder.file(cloud_path, size=size)
                    with open(local_path, "rb") as fp:
                        progress_callbacks.upload_start(local_path, cloud_file, size)
                        cloud_file.upload(fp, size, progress_callbacks.upload_progress)
                    progress_callbacks.upload_finish(cloud_file)
        progress_callbacks.finished()

    def bulk_download(self, paths, local_dir, progress_callbacks=None):
        """
        Transfer many files or directories to Cloud File System.
        paths - list of local file paths
        target - Path in CFS to upload to
        progress_callbacks - Callback object (see ProgressCallbacks)
        """
        if progress_callbacks is None:
            progress_callbacks = ProgressCallbacks()
        for path in paths:
            progress_callbacks.getting_info(path)
            obj = self.get(path)
            progress_callbacks.got_info(path, obj)
            if obj.is_folder:
                pass

        #while True:
        #    try:
        #        path = queue.popleft()
        #    except IndexError:
        #        # finished
        #        return
        #    if isinstance(path, base.HasClient):
        #        obj = path
        #    else:
        #        progress_callbacks.getting_info(path)
        #        obj = self.get(path)
        #        progress_callbacks.got_info(path, obj)
        #    if obj.is_folder:
        #        # schedule contents for later
        #        queue.extend(obj.files)
        #        queue.extend(obj.folders)
        #    else:


class ProgressCallbacks(object):
    """
    This object is used for bulk transfers (uploads and downloads)
    Inherit this and add override any of the callabcks you'd like to handle.
    """
    def getting_info(self, cloud_path):
        """Getting information about an object. Called for directories and unknown paths."""

    def got_info(self, cloud_obj):
        """Got information about an object."""

    def creating_directory(self, cloud_folder):
        """Creating a directory."""

    def download_start(self, local_path, cloud_file, size):
        """Starting to download a file."""

    def download_progress(self, cloud_file, size, downloaded):
        """Some progress in file download."""

    def download_finish(self, cloud_file):
        """Finished downloading a file."""

    def upload_start(self, local_path, cloud_file, size):
        """Starting to upload a file."""

    def upload_progress(self, cloud_file, size, uploaded):
        """Some progress in file upload."""

    def upload_finish(self, cloud_file):
        """Finished uploading a file."""

    def finished(self):
        """Called after all operations."""


        