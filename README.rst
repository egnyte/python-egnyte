Egnyte SDK
==========

This is the official Python client library for Egnyte.com Public APIs.

For overview of the API, go to https://developers.egnyte.com

Getting an API key
==================

Register on https://developers.egnyte.com/member/register to get API key
for your Egnyte account. This key is required to generate Egnyte OAuth
token.

Running tests
=============

Check doc/TESTS.md

Command line
============

You can generate API access token easily using command line options.
Check doc/COMMANDS.md for details.

Examples
========

examples subdirectory contains example code that should give you good
idea of how the client library can be used.

Helping with development
========================

First, report any problems you find to
https://developers.egnyte.com/forum/ or api-support@egnyte.com

If you'd like to fix something yourself, please fork this repository,
commit the fixes and updates to tests, then set up a pull request with
information what you're fixing.

Please remember to assign copyright of your fixes to Egnyte or make them
public domain so we can legally merge them.

Thread safety
=============

Each client object should be used from one thread at a time. This
library does no locking of it's own - it is responsibility of the caller
to do so if necessary.

Dependencies
============

This library depends on:

-  requests 2.2.1 or later - for HTTPS calls
-  six 1.8.0 or later - for Python 2 and 3 compatibility using same
   source

