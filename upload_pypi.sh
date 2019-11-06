#!/usr/bin/env bash
set -x
set -e
rm -rf dist
python3 -m nose dilawar || echo "Test failed" || echo "Test failed" || echo
"Test failed" || echo "Test failed"
python3 setup.py sdist 
python3 -m twine check dist/* && twine upload dist/*
