#!/usr/bin/env python
# -*- coding: utf-8 -*-

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

setup(
    name='egnyte',
    version='0.3',
    author=u'Vijayendra Bapte, Maciej Szumocki',
    author_email=u'api-support@egnyte.com',
    license='MIT',
    description='Egnyte Public API SDK',
    zip_safe=True,
    packages=["egnyte", "egnyte.tests", "egnyte.tests.integration"],
    url='https://developers.egnyte.com/',
    include_package_data=True,
    install_requires=[
        "requests>=2.2.1",
        "plac>=0.9.1",
    ],
    classifiers=[
        "Programming Language :: Python",
        "Programming Language :: Python :: 3",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    test_suite = 'egnyte.tests',
)
