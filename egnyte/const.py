SERVER = "egnyte.com"
BASE_URL = "https://%(domain)s.%(server)s"

LINK_KIND_FILE = "file"
LINK_KIND_FOLDER = "folder"
LINK_KIND_LIST = [
    LINK_KIND_FILE,
    LINK_KIND_FOLDER,
]


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
