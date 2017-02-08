#!/bin/bash
#
# This is the entry point for Jenkins.
# Script has do be called from "son-emu" root directory, like: sudo ./utils/ci/jenkins_entrypoint.sh
export DOCKER_HOST="unix:///var/run/docker.sock"

# don't rely on Debian/Ubuntu Docker engine
apt-get remove docker-engine
# make sure we start from scratch
pip uninstall docker-py
pip uninstall docker

set -e
set -x

SON_EMU_DIR=$(pwd)
cd $SON_EMU_DIR/../

# prepare
apt-get update
DEBIAN_FRONTEND=noninteractive apt-get install -o Dpkg::Options::="--force-confold" --force-yes -y git ansible aptitude
echo "localhost ansible_connection=local" >> /etc/ansible/hosts

# install containernet
git clone https://github.com/containernet/containernet.git
CONTAINERNET_DIR=$(pwd)/containernet
echo "Installing containernet (will take some time ~30 minutes) ..."
cd $CONTAINERNET_DIR/ansible
ansible-playbook install.yml

# install son-emu
echo "Installing son-emu (will take some time) ..."
cd $SON_EMU_DIR/ansible
ansible-playbook install.yml

# execute son-emu tests at the end to validate installation
echo "Running son-emu unit tests to validate installation"
cd $SON_EMU_DIR
python setup.py develop




