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
# This is the entry point for Jenkins.
# Script has to be called from "son-emu" root directory, like: sudo ./utils/ci/jenkins_entrypoint.sh
export DOCKER_HOST="unix:///var/run/docker.sock"

# don't rely on Debian/Ubuntu Docker engine
#apt-get remove docker-engine
# make sure we start from scratch
#pip uninstall docker-py
#pip uninstall docker

set -e
set -x

# install docker
apt-get install curl apt-transport-https ca-certificates
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
apt-get -qq update
apt-get install docker-ce

# build the container
docker build -t son-emu-img .

# launch the container and trigger the unit tests
docker run --name son-emu -it --rm --privileged --pid='host' -v /var/run/docker.sock:/var/run/docker.sock son-emu-img py.test -v src/emuvim/test/unittests

#
# old way to call the tests directly on the host machine
# 
#SON_EMU_DIR=$(pwd)
#cd $SON_EMU_DIR/../

# prepare
#apt-get update
#DEBIAN_FRONTEND=noninteractive apt-get install -o Dpkg::Options::="--force-confold" --force-yes -y git ansible aptitude
#echo "localhost ansible_connection=local" >> /etc/ansible/hosts

# install containernet
#git clone https://github.com/containernet/containernet.git
#CONTAINERNET_DIR=$(pwd)/containernet
#echo "Installing containernet (will take some time ~30 minutes) ..."
#cd $CONTAINERNET_DIR/ansible
#ansible-playbook install.yml

# install son-emu
#echo "Installing son-emu (will take some time) ..."
#cd $SON_EMU_DIR/ansible
#ansible-playbook install.yml

# execute son-emu tests at the end to validate installation
#echo "Running son-emu unit tests to validate installation"
#cd $SON_EMU_DIR
#python setup.py develop

# run the unit tests
#py.test -v src/emuvim/test/unittests


