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

import os

import time

from emuvim.api.osm.osm_component_base import OSMComponentBase
from emuvim.api.util.docker_utils import wrap_debian_like


class LCM(OSMComponentBase):
    def __init__(self, net, ip, ro_ip, mongo_ip, kafka_ip,
                 vca_host=os.environ.get('VCA_HOST'),
                 vca_secret=os.environ.get('VCA_SECRET'),
                 version='latest',
                 name_prefix=''):
        OSMComponentBase.__init__(self)
        self.instance = net.addDocker(
            '{}lcm'.format(name_prefix), ip=ip, dimage=wrap_debian_like('opensourcemano/lcm:%s' % version),
            volumes=['osm_packages:/app/storage'],
            environment={
                'OSMLCM_RO_HOST': ro_ip,
                'OSMLCM_VCA_HOST': vca_host,
                'OSMLCM_VCA_SECRET': vca_secret,
                'OSMLCM_DATABASE_URI': 'mongodb://%s:27017' % mongo_ip,
                'OSMLCM_MESSAGE_HOST': kafka_ip,
            })

    def start(self):
        OSMComponentBase.start(self)
        time.sleep(3)
