#!/usr/bin/env python2
# Copyright (c) 2019 Erik Schilling
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

from emuvim.api.osm.osm_component_base import OSMComponentBase
from emuvim.api.util.process_utils import wait_until


class Kafka(OSMComponentBase):
    def __init__(self, net, ip, zookeeper_ip, version='latest', name_prefix=''):
        OSMComponentBase.__init__(self)
        subnet_separator_index = ip.find('/')
        ip_without_subnet = ip if subnet_separator_index == -1 else ip[:subnet_separator_index]
        self.instance = net.addDocker(
            '{}kafka'.format(name_prefix), ip=ip, dimage='wurstmeister/kafka:%s' % version,
            environment={'KAFKA_ADVERTISED_HOST_NAME': ip_without_subnet,
                         'KAFKA_ADVERTISED_PORT': '9092',
                         'KAFKA_ZOOKEEPER_CONNECT': '%s:2181' % zookeeper_ip,
                         'KAFKA_CREATE_TOPICS': 'admin:1:1,ns:1:1,vim_account:1:1,wim_account:1:1,sdn:1:1,nsi:1:1'
                         })

    def start(self):
        OSMComponentBase.start(self)
        wait_until('nc -z %s 9092' % self.instance.dcinfo['NetworkSettings']['IPAddress'])
