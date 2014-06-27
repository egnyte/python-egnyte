# -*- coding: utf-8 -*-

import os
from setuptools import setup

setup(
    name='egnyte',
    version='0.2',
    author=u'Vijayendra Bapte',
    author_email='vbapte@egnyte.com',
    description='Egnyte SDK',
    zip_safe=False,
    packages=["egnyte", ],
    scripts=["egnyte/scripts/egnyte"],
    include_package_data=True,
    install_requires = ["requests",
                        "fabric",
                        "keyring",
                        "setuptools",
                        "nose",
                        "nose-testconfig",
                        "coverage",
                        "plac",
                        ],
    )
