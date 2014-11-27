Egnyte SDK
==========

This is the official Python client library for Egnyte.com Public APIs.
For overview of the API, go to https://developers.egnyte.com

Getting an API key
==================

Register on https://developers.egnyte.com/member/register to get API key
for your Egnyte account. This key is required to generate Egnyte OAuth
token.

Examples
========

.. code-block:: python

    from egnyte import EgnyteClient
    client = EgnyteClient({"domain": "<your domain here>.egnyte.com", "access_token": "<your access token here"})
    folder = client.folder("/Shared/foo that need to be bar")
    for f in folder.list().files:
        data = f.download().read()
        f.upload(data.replace(b"foo", b"bar"))
        f.add_note("all occurrences of 'foo' replaced by 'bar'!")

examples subdirectory contains example code that should give you good
idea of how the client library can be used.

Command line
============

If you're using implicit flow, you'll need to provide access token directly.
If you're using API token with resource flow, you can generate API access token using command line options.
Check doc/COMMANDS_ for details.

Dependencies
============

This library depends on:

-  requests 2.2.1 or later - for HTTPS calls
-  six 1.8.0 or later - for Python 2 and 3 compatibility using same
   source

Thread safety
=============

Each client object should be used from one thread at a time. This
library does no locking of it's own - it is responsibility of the caller
to do so if necessary.

Running tests
=============

Check doc/TESTS_

Helping with development
========================

First, report any problems you find to
https://developers.egnyte.com/forum/ or api-support@egnyte.com

If you'd like to fix something yourself, please fork this repository,
commit the fixes and updates to tests, then set up a pull request with
information what you're fixing.

Please remember to assign copyright of your fixes to Egnyte or make them
public domain so we can legally merge them.
