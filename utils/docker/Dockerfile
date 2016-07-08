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

FROM mpeuster/containernet
MAINTAINER manuel@peuster.de

ENV SON_EMU_IN_DOCKER 1

WORKDIR /son-emu
COPY . /son-emu/

RUN apt-get clean

RUN cd /son-emu/ansible \
    && ansible-playbook install.yml \
    && cd /son-emu \
    # we need to reset the __pycache__ for correct test discovery
    && rm -rf src/emuvim/test/__pycache__ \
    && rm -rf src/emuvim/test/unittests/__pycache__ \
    && rm -rf src/emuvim/test/integrationtests/__pycache__ \
    && python setup.py install \
    && echo 'Done'

ENTRYPOINT ["/son-emu/utils/docker/entrypoint.sh"]

# dummy GK, zerorpc, DCNetwork zerorpc, cAdvisor
EXPOSE 5000 4242 5151 8090
