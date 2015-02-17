#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os.path

from setuptools import setup

with open(os.path.join(os.path.dirname(__file__), "README.rst"), "rt") as f:
    long_description = f.read()

args = dict(
    name='egnyte',
    version='0.5',
    author='Vijayendra Bapte, Maciej Szumocki',
    author_email='api-support@egnyte.com',
    license='MIT',
    description='Egnyte Public API SDK',
    long_description=long_description,
    zip_safe=True,
    packages=["egnyte", "egnyte.tests"],
    url='https://developers.egnyte.com/',
    include_package_data=True,
    install_requires=[
        "requests>=2.2.1",
        "six>=1.8.0",
    ],
    platforms = ["Any"],
    classifiers=[
        "Programming Language :: Python :: 2.7",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
    test_suite="egnyte",
    extras_require={
        'docs': ['sphinx', 'sphinx-argparse'],
    },
    # TODO: add an entrypoint for a console script, or do we stick with 'python -m egnyte'?
)

if __name__ == '__main__':
    setup(**args)
