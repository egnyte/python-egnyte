from fabric.api import *
from fabric.context_managers import *

env.package_name = "egnyte"

def clean():
    """
    Cleanup .pyc *~ files and build related directories
    """
    local("rm -rf dist build dist *.egg-info cover")
    local("find . \( ! -regex '.*/\..*/..*' \) -type f -name '*.pyc' -exec rm '{}' +")
    local("find . \( ! -regex '.*/\..*/..*' \) -type f -name '*~' -exec rm '{}' +")

def tar():
    """
    Create python source distribution .tar.gz
    """
    clean()
    local('mkdir dist')
    local('git archive --prefix=%(package_name)s/ --format=tar master | gzip > dist/%(package_name)s.tar.gz' % env)

def sdist():
    """
    Create python source distribution .tar.gz
    """
    clean()
    local("python setup.py sdist")

def egg():
    """
    Create .egg python distribution file.
    """
    clean()
    local("python setup.py bdist_egg")

def setup(kind):
    """
    setup:egg or setup:sdist
    """
    if kind == "egg":
        egg()
    elif kind == "sdist":
        sdist()

def install():
    """
    Install .egg created using egg command.
    """
    local("easy_install dist/*.egg")

def test():
    """
    Run basic unittests
    """
    with lcd(env.package_name):
        local("nosetests -v --tc-file tests/local_config.ini --with-coverage --nocapture --cover-package=%(package_name)s" % env)
        #local("nosetests -v --with-coverage --cover-package=%(package_name)s" % env)

def reinstall():
    """
    Install .egg created using egg command.
    """
    clean()
    egg()
    install()
    clean()
