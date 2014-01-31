# Egnyte SDK

# HOWTO:

## Install:

    $ easy_install egnyte-0.1-py2.7.egg


## Get help

    $ ezshare -h
    Usage: ezshare [options]

    Options:
      -h, --help            show this help message and exit
      -u USER, --user=USER  specify user name e.g myname@domain
      -f FILEPATH, --filepath=FILEPATH
                            path of file which you want to share

## Upload file:

    $ ezshare -u vijayendra@bapte -f /tmp/test.txt 

    Enter password: <YOUR-EGNYTE-PASSWORD>
    Enter Api Key: <YOUR-API-KEY>
    File uploaded: /tmp/test.txt
    Ezshare link: https://bapte.egnyte.com/h-s/20140131/d75c88db9d2d48e0

## Tests:

Follow ./egnyte/tests/*.py to understand how to work with egnyte SDK
