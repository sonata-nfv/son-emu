# Copyright (c) 2017 SONATA-NFV and Paderborn University
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

FROM ubuntu:xenial

ENV SON_EMU_IN_DOCKER 1
ENV PIP_DEFAULT_TIMEOUT=100

# install required packages
RUN apt-get clean
RUN apt-get update \
    && apt-get install -y  git \
    net-tools \
    aptitude \
    build-essential \
    python-setuptools \
    python-dev \
    python-pip \
    software-properties-common \
    ansible \
    curl \
    iptables \
    iputils-ping \
    sudo

# install containernet (using its Ansible playbook)
# Attention: Containernet installation fixed to specific commit. Change to update to latest Containernet version.
RUN git clone https://github.com/containernet/containernet.git && \
    (cd containernet && git checkout 6fcee82e192c8c0e6447650d6f512842185529ee)
WORKDIR /containernet/ansible
RUN ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml

# install emulator (using its Ansible playbook)
COPY . /son-emu
WORKDIR /son-emu/ansible
RUN ansible-playbook -i "localhost," -c local --skip-tags "notindocker" install.yml
WORKDIR /son-emu
RUN python setup.py develop

# Hotfix: https://github.com/pytest-dev/pytest/issues/4770
RUN pip2 install "more-itertools<=5.0.0"

# Important: This entrypoint is required to start the OVS service
ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]
CMD ["python", "examples/default_single_dc_topology.py"]

# open ports for emulator APIs
# SONATA GK
EXPOSE 5000
# EMU REST API
EXPOSE 5001
# Monitoring (Prometheus)
EXPOSE 8081
# Monitoring (GW)
EXPOSE 9091
# OpenStack-fake
EXPOSE 4000
# OpenStack-fake
EXPOSE 10243
# OpenStack-fake
EXPOSE 9005
# OpenStack-fake (Keystone)
EXPOSE 6001
# OpenStack-fake
EXPOSE 9775
# OpenStack-fake
EXPOSE 10697
