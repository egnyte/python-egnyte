import os.path
import json


def add_directory(filepath):
    """
    Add '~/.egnyte' in a platform independent way to a file path it it's relative.
    """
    if os.path.isabs(filepath):
        return filepath
    return os.path.join(os.path.expanduser('~'), '.egnyte', filepath)


def load(filename=None):
    """
    Load configuration from a JSON file.
    If filename is None, ~/.egnyte/config.json will be loaded.
    If filename is not an absolute path, it will be prefixed with ~/.egnyte/
    Returns loaded config as a dictionary on success and {} on failure.
    """
    filename = add_directory(filename or 'config.json')
    try:
        with open(filename, "r") as f:
            return json.load(f)
    except IOError:
        pass
    return {}


def save(config, filename=None):
    """
    Load configuration from a JSON file.
    If filename is not an absolute path, it will be prefixed with ~/.egnyte/
    """
    filename = add_directory(filename or 'config.json')
    directory = os.path.dirname(filename)
    if not os.path.exists(directory):
        os.makedirs(directory, 0o700)
    with open(filename, "w") as f:
        json.dump(config, f, indent=2, sort_keys=True)
