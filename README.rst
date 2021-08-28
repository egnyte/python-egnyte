Egnyte SDK
==========

This is the official Python client library for Egnyte's Public APIs.
For overview of the HTTP API, go to https://developers.egnyte.com

Getting an API key
==================

Register on https://developers.egnyte.com/member/register to get API key
for your Egnyte account. This key is required to generate an Egnyte OAuth
token.

Examples
========

* Include this library

.. code-block::python

    import egnyte

* Generate an access token

.. code-block::python

    egnyte.base.get_access_token({"api_key":"cba97f3apst9eqzdr5hskggx", "login":"test", "password":"password", "grant_type":"password", "domain":"apidemo"})

* Create a client object

.. code-block:: python

    client = egnyte.EgnyteClient({"domain": "apidemo.egnyte.com",
        "access_token": "68zc95e3xv954u6k3hbnma3q"})

* Create a folder

.. code-block:: python

    folder = client.folder("/Shared/new").create(ignore_if_exists=True)

* Delete a folder

.. code-block:: python

    client.folder("/Shared/time to say goodbye").delete()

* Get a list of files in a folder, download a file, replace it's contents, add a note

.. code-block:: python

    folder = client.folder("/Shared/foo that need to be bar")
    folder.list()
    for file_obj in folder.files:
        with file_obj.download() as download:
            data = download.read()
        # replace file contents
        file_obj.upload(data.replace(b"foo", b"bar"))
        file_obj.add_note("all occurrences of 'foo' replaced by 'bar'!")

* Get a list of files in a subfolders

.. code-block:: python

    folder = client.folder("/Shared")
    folder.list()
    for folder_obj in folder.folders:
        do_something(folder_obj)

* Upload a new file from local file

.. code-block:: python

    file_obj = client.file("/Private/smeagol/my precious")
    with open("local path", "rb") as fp:
        file_obj.upload(fp)

* Delete a file

.. code-block:: python

    file_obj.delete()

* Do a recursive download

.. code-block:: python

    client.bulk_download(['/Shared/a dir', '/Shared/another dir'],
        '/home/smeagol/', overwrite=True)

* Do a recursive upload

.. code-block:: python

    client.bulk_upload(['/tmp/some directory', '/tmp/some file'], '/Shared/Marketing')

* Search for files

.. code-block:: python

    import datetime
    results = api.search.files('"some text" OR "other text"', folder='/Shared', modified_after=datetime.date(2015, 1, 15))

* Get and process events from server

.. code-block:: python

    events = api.events.filter(folder='/Shared', suppress='user')
    old_events = events.list(events.latest_event_id - 10, count = 10) # get events in batches
    future_events = iter(events)
    for event in future_events: # polls server continously, iterator over single events, iterator will never end
        do_something(event)
        if condition(event):
            break



Full documentation
==================

The docs subdirectory contains just the source for the documentation.
You can read the documentation at http://egnyte.github.io/python-egnyte/


Command line
============

If you're using implicit flow, you'll need to provide access token directly.
If you're using API token with resource flow, you can generate API access token using command line options.
See the full documentation or install, then use:

.. code-block:: python

    python -m egnyte -h

Create configuration
====================

Configuration file will be created in ~/.egnyte/config.json

.. code-block:: python

    python -m egnyte config create -d DOMAIN [-l LOGIN] [-p PASSWORD] -k API_KEY [-t ACCESS_TOKEN] [-T TIMEOUT]

Set request timeout
===================

.. code-block:: python

    python -m egnyte config update --timeout TIMEOUT_INTEGER

Dependencies
============

This library depends on:

-  Python 3.6-3.9
-  requests 2.13.0 or later

Thread safety
=============

Each client object should be used from one thread at a time. This
library does no locking of it's own - it is responsibility of the caller
to do so if necessary.

Running tests
=============

Tests can be run with nose or trial directly on the egnyte package, or
from setup.py:

.. code-block:: python

    python setup.py test

or

.. code-block:: python

    python -m unittest discover

In order to run tests, you need to create test configuration file: ~/.egnyte/test\_config.json

.. code-block:: json

    {
        "access_token": "access token you received after passing the auth flow", 
        "api_key": "key you received after registering your developer account", 
        "domain": "your Egnyte domain, e.g. example.egnyte.com", 
        "login": "username of Egnyte admin user", 
        "password": "password of the same Egnyte admin user"
    }

You can create this file manually or with following command:

.. code-block:: python

    python -m egnyte -c test_config.json config create -k <API_Key> -d <domain> -l <username> -p <password> -t <access_token>

Tests will be run against your domain on behalf on admin user.

Please refer to https://developers.egnyte.com/docs/read/Public_API_Authentication#Internal-Applications for information
about how to generate access token.

Helping with development
========================

Please report any problems you find to
api-support@egnyte.com or pint@egnyte.com

If you'd like to fix something yourself, please fork this repository,
commit the fixes and updates to tests, then set up a pull request with
information what you're fixing.

Please remember to assign copyright of your fixes to Egnyte or make them
public domain so we can legally merge them.
