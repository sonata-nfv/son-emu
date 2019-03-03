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
from emuvim.api.util.docker_utils import wrap_debian_like
from emuvim.api.util.process_utils import wait_until


class RO(OSMComponentBase):
    def __init__(self, net, ip, db_ip, version='latest', name_prefix=''):
        OSMComponentBase.__init__(self)
        self.instance = net.addDocker(
            '{}ro'.format(name_prefix), ip=ip, dimage=wrap_debian_like('opensourcemano/ro:%s' % version),
            environment={'RO_DB_HOST': db_ip, 'RO_DB_ROOT_PASSWORD': 'TEST'})

    def start(self):
        OSMComponentBase.start(self)
        wait_until('nc -z %s 9090' % self.instance.dcinfo['NetworkSettings']['IPAddress'])
