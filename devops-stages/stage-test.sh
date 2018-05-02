#!/bin/bash
#
# Runs the unittests of "vim-emu". Script needs to be executed inside
# the vim-emu Docker container by user "root". It requires the container
# to be started in privileged mode.
#
set -e
echo "vim-emu stage-test"
# trigger ovs setup since container entrypoint is overwritten by Jenkins
service openvswitch-switch start
# ensure the Docker image used during the unittests is there
docker pull 'ubuntu:trusty'
# debugging
echo "Tests executed inside: $(hostname)"
echo "Tests executed by user: $(whoami)"
# trigger the tests
cd /son-emu/
py.test -v src/emuvim/test/unittests

