import os


def upload_file(egnyte, filename, cloud_file_path):
    source = open(get_file_path(filename), 'rb')
    uploaded_file = egnyte.file(cloud_file_path)
    uploaded_file.upload(source)
    return uploaded_file


def get_file_path(filename):
    return os.path.join(os.getcwd(), 'egnyte', 'tests', 'data', filename)
