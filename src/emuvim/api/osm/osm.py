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

from emuvim.api.openstack.resources.net import Net
from emuvim.api.osm.kafka import Kafka
from emuvim.api.osm.lcm import LCM
from emuvim.api.osm.mongo import Mongo
from emuvim.api.osm.mysql import Mysql
from emuvim.api.osm.nbi import NBI
from emuvim.api.osm.ro import RO
from emuvim.api.osm.zookeeper import Zookeeper


class OSM:
    def __init__(self, net,
                 switch,
                 name='osm',
                 vca_host=os.environ.get('VCA_HOST'),
                 vca_secret=os.environ.get('VCA_SECRET'),
                 osm_version='releasefive-daily',
                 ip_start='10.0.0.100'):
        ip_int = Net.ip_2_int(ip_start)
        zookeeper_ip = ip_start
        kafka_ip = Net.int_2_ip(ip_int + 1)
        mongo_ip = Net.int_2_ip(ip_int + 2)
        nbi_ip = Net.int_2_ip(ip_int + 3)
        ro_db_ip = Net.int_2_ip(ip_int + 4)
        ro_ip = Net.int_2_ip(ip_int + 5)
        lcm_ip = Net.int_2_ip(ip_int + 6)

        name_prefix = '%s-' % name
        self.zookeeper = Zookeeper(net, '%s/16' % zookeeper_ip, name_prefix=name_prefix)
        self.kafka = Kafka(net, '%s/16' % kafka_ip, zookeeper_ip, name_prefix=name_prefix)
        self.mongo = Mongo(net, '%s/16' % mongo_ip, name_prefix=name_prefix)
        self.nbi = NBI(net, '%s/16' % nbi_ip, mongo_ip, kafka_ip, version=osm_version, name_prefix=name_prefix)
        self.ro_db = Mysql(net, '%s/16' % ro_db_ip, name_prefix=name_prefix)
        self.ro = RO(net, '%s/16' % ro_ip, ro_db_ip, version=osm_version, name_prefix=name_prefix)
        self.lcm = LCM(net, '%s/16' % lcm_ip, ro_ip, mongo_ip, kafka_ip,
                       vca_host, vca_secret, version=osm_version, name_prefix=name_prefix)

        net.addLink(self.zookeeper.instance, switch)
        net.addLink(self.kafka.instance, switch)
        net.addLink(self.mongo.instance, switch)
        net.addLink(self.nbi.instance, switch)
        net.addLink(self.ro_db.instance, switch)
        net.addLink(self.ro.instance, switch)
        net.addLink(self.lcm.instance, switch)

    def start(self):
        self.zookeeper.start()
        self.kafka.start()
        self.mongo.start()
        self.nbi.start()
        self.ro_db.start()
        self.ro.start()
        self.lcm.start()

    # forward api related calls
    def onboard_vnfd(self, *args, **kwargs):
        return self.nbi.onboard_vnfd(*args, **kwargs)

    def onboard_nsd(self, *args, **kwargs):
        return self.nbi.onboard_nsd(*args, **kwargs)

    def register_emulated_api(self, *args, **kwargs):
        return self.nbi.register_emulated_api(*args, **kwargs)

    def ns_list(self):
        return self.nbi.ns_list()

    def ns_create(self, *args, **kwargs):
        return self.nbi.ns_create(*args, **kwargs)

    def ns_delete(self, *args, **kwargs):
        return self.nbi.ns_delete(*args, **kwargs)

    def ns_get(self, *args, **kwargs):
        return self.nbi.ns_get(*args, **kwargs)

    def ns_action(self, *args, **kwargs):
        return self.nbi.ns_action(*args, **kwargs)

    def ns_wait_until_all_in_status(self, *args, **kwargs):
        return self.nbi.ns_wait_until_all_in_status(*args, **kwargs)
