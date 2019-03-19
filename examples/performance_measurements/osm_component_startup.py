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
import csv

import time

from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from emuvim.api.osm.kafka import Kafka
from emuvim.api.osm.lcm import LCM
from emuvim.api.osm.mongo import Mongo
from emuvim.api.osm.mysql import Mysql
from emuvim.api.osm.nbi import NBI
from emuvim.api.osm.ro import RO
from emuvim.api.osm.zookeeper import Zookeeper
from emuvim.dcemulator.net import DCNetwork


from mininet.log import setLogLevel
setLogLevel('debug')

COUNT = 15

with open('osm_component_startup_%d.csv' % time.time(), 'w') as csvfile:
    fieldnames = ['other', 'zookeeper', 'kafka', 'mongo', 'nbi', 'ro_db', 'ro', 'lcm']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for i in range(COUNT):
        start = time.time()
        net = DCNetwork(monitor=False, enable_learning=True)
        api = None
        try:
            dc1 = net.addDatacenter("dc1")
            api = OpenstackApiEndpoint("0.0.0.0", 6001)
            api.connect_datacenter(dc1)
            api.connect_dc_network(net)

            s1 = net.addSwitch('s1')

            zookeeper_ip = '10.0.0.96'
            kafka_ip = '10.0.0.97'
            mongo_ip = '10.0.0.98'
            nbi_ip = '10.0.0.99'
            ro_db_ip = '10.0.0.100'
            ro_ip = '10.0.0.101'
            lcm_ip = '10.0.0.102'

            d1 = net.addDocker('d1', dimage='ubuntu:trusty')

            VERSION = 'releasefive-daily'

            zookeeper = Zookeeper(net, zookeeper_ip)
            kafka = Kafka(net, kafka_ip, zookeeper_ip)
            mongo = Mongo(net, mongo_ip)
            nbi = NBI(net, nbi_ip, mongo_ip, kafka_ip)
            ro_db = Mysql(net, ro_db_ip)
            ro = RO(net, ro_ip, ro_db_ip, version=VERSION)
            lcm = LCM(net, lcm_ip, ro_ip, mongo_ip, kafka_ip)

            net.addLink(d1, s1)
            net.addLink(zookeeper.instance, s1)
            net.addLink(kafka.instance, s1)
            net.addLink(mongo.instance, s1)
            net.addLink(nbi.instance, s1)
            net.addLink(ro_db.instance, s1)
            net.addLink(ro.instance, s1)
            net.addLink(lcm.instance, s1)

            net.start()
            api.start()

            other_end = time.time()
            zookeeper.start()
            zookeeper_started = time.time()
            kafka.start()
            kafka_started = time.time()
            mongo.start()
            mongo_started = time.time()
            nbi.start()
            nbi_started = time.time()
            ro_db.start()
            ro_db_started = time.time()
            ro.start()
            ro_started = time.time()
            lcm.start()
            lcm_started = time.time()

            writer.writerow({
                'other': other_end - start,
                'zookeeper': zookeeper_started - other_end,
                'kafka': kafka_started - zookeeper_started,
                'mongo': mongo_started - kafka_started,
                'nbi': nbi_started - mongo_started,
                'ro_db': ro_db_started - nbi_started,
                'ro': ro_started - ro_db_started,
                'lcm': lcm_started - ro_started,
            })
            csvfile.flush()
        finally:
            net.stop()
            api.stop()
