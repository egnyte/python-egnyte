#!/bin/bash

git clone --depth=1 ssh://git@git.egnyte-internal.com/integrations/pint-runner-environment.git

if [ -d "~/.egnyte" ]; then
    rm -r ~/.egnyte
fi

mkdir ~/.egnyte
cp ./pint-runner-environment/egnyte-python-sdk/test_config.json ~/.egnyte/test_config.json
virtualenv venv
source venv/bin/activate
pip install -r requirements.txt
python setup.py nosetests --verbosity=2 --with-coverage --cover-package egnyte
EXITCODE=$?
deactivate
exit $EXITCODE