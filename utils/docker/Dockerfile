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
# Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).

FROM ubuntu:trusty
MAINTAINER steven.vanrossem@intec.ugent.be

ENV SON_EMU_IN_DOCKER 1

RUN apt-get clean
RUN apt-get update \
    && apt-get install -y  git aptitude


# install containernet
RUN apt-get install -y curl && \
    curl https://bootstrap.pypa.io/get-pip.py | python2

# install docker
RUN curl -fsSL https://get.docker.com/gpg | apt-key add -
RUN curl -fsSL https://get.docker.com/ | sh

RUN pip install -U urllib3 setuptools pyparsing docker python-iptables
WORKDIR /
RUN git clone https://github.com/containernet/containernet.git
RUN containernet/util/install.sh
WORKDIR containernet/
RUN make develop

# install son-emu
RUN echo 'install son-emu'
RUN apt-get install -y  python-dev python-zmq libzmq-dev libffi-dev libssl-dev
RUN pip install -U zerorpc tabulate argparse networkx six ryu oslo.config pytest Flask flask_restful requests prometheus_client pyaml
WORKDIR /
#avoid pulling not the latest git, copy the current dir, to run this from Jenkins
#RUN git clone https://github.com/sonata-nfv/son-emu.git
COPY . /son-emu
WORKDIR son-emu/
RUN python setup.py develop
WORKDIR / 
RUN echo 'Done'


ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]

# dummy GK, cAdvisor, Prometheus Push Gateway, son-emu REST API
EXPOSE 5000 8081 9091 5001
