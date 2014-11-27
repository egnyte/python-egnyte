#!/bin/sh
pandoc --from=markdown --to=rst --output=$1.rst $1.md
