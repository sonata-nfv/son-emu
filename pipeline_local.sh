#!/bin/bash
# helper script to be executed before committing
set -e
# trigger pep8 style check
echo "Doing flake8 style check ..."
flake8 --exclude=.eggs,devops --ignore=E501 .
echo "done."
# trigger the tests
echo "Running unit tests ..."
sudo pytest -v
echo "done."
