"""
Exceptions and their handlers.
"""

from six.moves import http_client

__all__ = """
EgnyteError InvalidParameters InsufficientPermissions NotFound Redirected NotAuthorized JsonParseError DomainRequired ClientIdRequired
OAuthUsernameRequired OAuthPasswordRequired UnsupportedAuthStrategy RequestError DuplicateRecordExists FileSizeExceedsLimit ChecksumError
""".split()

class EgnyteError(Exception):
    """Base class for Egnyte SDK exceptions"""

    def __str__(self):
        """Pretty-printed version. Use repr for bare vesion instead"""
        contents = []
        for item in self:
            if isinstance(item, dict):
                contents.append("{%s}" % ", ".join(sorted(["%s: '%s'" % (k, v) for (k, v) in item.items()])))
            else:
                contents.append(str(item))
        return "<%s: %s>" % (self.__class__.__name__, ", ".join(contents))


class InvalidParameters(EgnyteError):
    """Invalid parameters were passed to an API request"""


class InsufficientPermissions(EgnyteError):
    """User does not have sufficient permissions to perform this action"""


class NotFound(EgnyteError):
    """Resource with name does not exist"""


class Redirected(EgnyteError):
    """Received unexpected HTTP 303 response"""


class NotAuthorized(EgnyteError):
    """Access token is required"""


class JsonParseError(EgnyteError):
    """Response from the server could not be parsed properly"""


class DomainRequired(EgnyteError):
    """Domain name is required"""


class ClientIdRequired(EgnyteError):
    """Client id is required"""


class OAuthUsernameRequired(EgnyteError):
    """Username is required for OAuth authentication"""


class OAuthPasswordRequired(EgnyteError):
    """Password is required for OAuth authentication"""


class UnsupportedAuthStrategy(EgnyteError):
    """This OAuth flow is not supported by this API key"""


class RequestError(EgnyteError):
    """Other kinds of request errors"""


class FileExpected(EgnyteError):
    """
    """


class DuplicateRecordExists(EgnyteError):
    """Existing entity conflict"""


class FileSizeExceedsLimit(EgnyteError):
    """File is too large for this operation."""


class ChecksumError(EgnyteError):
    """Checksum of the uploaded file is different than checksum calculated locally - file was corrupted during transfer."""

def extract_errors(data):
    """
    Try to extract useful information from inconsistent error data structures.
    """
    if 'errors' in data:
        data = data['errors']
    if 'inputErrors' in data:
        for err in extract_errors(data['inputErrors']):
            yield err
    elif hasattr(data, 'keys'):
        if 'code' in data:
            yield data
        else:
            for value in data.values():
                for err in extract_errors(value):
                    yield err
    elif isinstance(data, list):
        for value in data:
            for err in extract_errors(value):
                yield err
    else:
        yield data


def recursive_tuple(data):
    """Convert nested lists/dicts into tuples for structural comparing"""
    if isinstance(data, (list, tuple)):
        return tuple(recursive_tuple(x) for x in data)
    elif isinstance(data, dict):
        # We cannot use plain tuple(sorted(...)) here, because while it works giving us stable sort
        # in Python 2.7, it does not in Python 3 (results in TypeError: unorderable types
        # so we'll sort dictonaries first and then turn into tuples
        return tuple((recursive_tuple(x), recursive_tuple(y)) for (x, y) in sorted(data.items()))
    return data


class ErrorMapping(dict):
    """Maps HTTP status to EgnyteError subclasses"""
    ignored_errors = ()

    def __init__(self, values=None, ok_statuses=(http_client.OK, ), ignored_errors=None):
        super(ErrorMapping, self).__init__({
            http_client.BAD_REQUEST: RequestError,
            http_client.UNAUTHORIZED: NotAuthorized,
            http_client.FORBIDDEN: InsufficientPermissions,
            http_client.NOT_FOUND: NotFound,
            http_client.CONFLICT: DuplicateRecordExists,
            http_client.REQUEST_ENTITY_TOO_LARGE: FileSizeExceedsLimit,
            http_client.SEE_OTHER: Redirected,
        })
        if values:
            self.update(values)
        if ignored_errors:
            self.ignored_errors = recursive_tuple(ignored_errors)
        self.ok_statuses = ok_statuses

    def map_error(self, response):
        return self.get(response.status_code, RequestError)

    def check_response(self, response, *ok_statuses):
        """
        Check if HTTP response has a correct status,
        try to raise a specific EgnyteError subclass if not
        """
        if not len(ok_statuses):
            ok_statuses = self.ok_statuses
        if response.status_code not in ok_statuses:
            errors = [{'url': response.url}]
            error_type = self.map_error(response)
            try:
                data = response.json()
                for err in extract_errors(data):
                    errors.append(err)
            except Exception:
                errors.append({"http response": response.text})
            errors.append({"http status": response.status_code})
            errors.append({"headers": dict(response.headers)})
            if not self.ignore_error(errors):
                raise error_type(*errors)
        return response

    def ignore_error(self, errors):
        errors = recursive_tuple(errors[1:])
        if errors and self.ignored_errors:
            result = any((errors[:len(ignored)] == ignored) for ignored in self.ignored_errors)
            return result

    def check_json_response(self, response, *ok_statuses):
        """
        Check if HTTP response has a correct status and then parse it as JSON,
        try to raise a specific EgnyteError subclass if not
        """
        try:
            r = self.check_response(response, *ok_statuses)
            if r.status_code == http_client.NO_CONTENT:
                return None
            return r.json()
        except ValueError:
            raise JsonParseError({"http response": response.text})

    def copy(self):
        """Make a copy preserving class of self"""
        return self.__class__(self)

default = ErrorMapping()
partial = ErrorMapping(ok_statuses={http_client.PARTIAL_CONTENT})
accepted = ErrorMapping(ok_statuses={http_client.ACCEPTED})
created = ErrorMapping(ok_statuses={http_client.CREATED})
no_content_ok = ErrorMapping(ok_statuses={http_client.OK, http_client.NO_CONTENT})
created_ignore_existing = ErrorMapping(ok_statuses=(http_client.CREATED,), ignored_errors = [
    (u'Folder already exists at this location', {'http status': 403})
])
