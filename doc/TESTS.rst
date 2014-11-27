Tests
-----

Tests can be run with nose or trial directly on the egnyte package, or
from setup.py:

python setup.py test

or

python setyp.py nosetests

Integration tests will be skipped unless you create
~/.egnyte/test\_config.json

You can create this file manually or with following command:

python -m egnyte -c test\_config.json config create -k -d -l [-p ]
