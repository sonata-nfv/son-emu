#!/bin/bash
# helper script to be executed before committing
set -e
# trigger pep8 style check
echo "Doing flake8 style check ..."
flake8 --exclude=.eggs,devops,examples/charms --ignore=E501,W605,W504 .
echo "done."
# trigger the tests
echo "Running unit tests ..."
sudo pytest -v
# do everything in Docker, like it is done by Jenkins
docker build -t vim-emu-loc-test .
docker run --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock vim-emu-loc-test pytest -v
docker run --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock vim-emu-loc-test flake8 --exclude=.eggs,devops,examples/charms --ignore=E501,W605,W504 .
echo "done."
