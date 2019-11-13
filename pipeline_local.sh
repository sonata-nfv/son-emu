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


# helper script to be executed before committing
set -e
# trigger pep8 style check
echo "Doing flake8 style check ..."
flake8 --exclude=.eggs,build,devops,examples/charms --ignore=E501,W605,W504 .
echo "done."
# trigger the tests
echo "Running unit tests ..."
sudo pytest -v
# do everything in Docker, like it is done by Jenkins
docker build -t vim-emu-loc-test .
docker run --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock vim-emu-loc-test pip list
docker run --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock vim-emu-loc-test pytest -v
docker run --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock vim-emu-loc-test flake8 --exclude=.eggs,devopsi,build,examples/charms --ignore=E501,W605,W504 .
echo "done."
