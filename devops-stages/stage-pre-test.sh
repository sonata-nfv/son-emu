#!/bin/bash
# Copyright (c) 2015 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# Runs the unittests of "vim-emu". Script needs to be executed inside
# the vim-emu Docker container by user "root". It requires the container
# to be started in privileged mode.
#
set -e
echo "vim-emu stage-pre-test.sh"
exit 1 # lets fail here




# debugging
echo "stage-test.sh executed inside: $(hostname)"
echo "stage-test.sh executed by user: $(whoami)"
# disable root-required test for now to play around some more.
echo "Stopping early."
exit 0

# Attention: The following needs to be done as root
# trigger ovs setup since container entrypoint is overwritten by Jenkins
service openvswitch-switch start
# ensure the Docker image used during the unittests is there
docker pull 'ubuntu:trusty'

cd /son-emu/
# trigger pep8 style check
echo "flake8 version:"
flake8 --version
echo "Doing flake8 style check ..."
flake8 --exclude=.eggs,devops,build,examples/charms --ignore=E501,W605,W504 .
echo "done."
# trigger the tests
echo "Running unit tests ..."
pytest -v
echo "done."



