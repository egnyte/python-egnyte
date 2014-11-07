# Egnyte SDK

# HOWTO

## Get API key

Register on https://developers.egnyte.com/member/register to get API key for your Egnyte account.
This key is required to generate egnyte oAuth token.


## Tests

Tests can be run with nose or trial directly on the egnyte package, or from setup.py:

python setup.py test

or

python setyp.py nosetests

Integration tests will be skipped unless you create ~/.egnyte/test_config.ini

You can create this file manually (use egnyte/tests/config.ini as a template) or after installing
with following command:

python -m egnyte config tests <api key> <username>:<password>@<domain>


## Command line

python -m egnyte config set <api key> <username>:<password>@<domain>
python -m egnyte config show
python -m egnyte test




