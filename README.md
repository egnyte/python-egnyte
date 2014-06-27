# Egnyte SDK

# HOWTO

## Install

    $ easy_install egnyte-0.2-py2.7.egg

## Get API key

Register on https://developers.egnyte.com/member/register to get API key for your Egnyte account.
This key is required to generate egnyte oAuth token.

## How to use it?

You need it first use `init` command to initialize egnyte sdk. Then verify that
all config is correct using `show` command. Then you can share files using
`share` command

    $ egnyte init vbapte egnyte <api-key>
    Enter the password: <my egnyte account password>
    $ egnyte show
    $ egnyte share /path/to/file

## How to get help?

    $ egnyte -h

    special commands
    ================
    .last_tb

    custom commands
    ===============
    get_access_token  help  init  share  show

    $ egnyte init -h
    usage: egnyte init [-h] [-token None] [-server egnyte.com] username domain api_key

    positional arguments:
      username            username
      domain              domain
      api_key             api_key

    optional arguments:
      -h, --help          show this help message and exit
      -token None         token
      -server egnyte.com  server

    $ egnyte share -h
    usage: egnyte share [-h] [-folderpath None] filepath

    positional arguments:
      filepath          filepath

    optional arguments:
      -h, --help        show this help message and exit
      -folderpath None  filepath

## Tests

    $ fab test

# TODO

1. List Links api (last one): https://developers.egnyte.com/docs/Egnyte_Link_API_Documentation 
2. User management api: https://developers.egnyte.com/docs/User_Management_API_Documentation
3. Report management api: https://developers.egnyte.com/docs/Egnyte_Audit_Reporting_API_v1

