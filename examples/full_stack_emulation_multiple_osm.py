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


from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from emuvim.api.osm.osm import OSM
from emuvim.dcemulator.net import DCNetwork

net = DCNetwork(monitor=False, enable_learning=True)
dc1 = net.addDatacenter("dc1")
api = OpenstackApiEndpoint("0.0.0.0", 6001)
api.connect_datacenter(dc1)
api.connect_dc_network(net)

try:
    s1 = net.addSwitch('s1')
    s2 = net.addSwitch('s2')
    osm1 = OSM(net, s1, name='1')
    osm2 = OSM(net, s2, name='2')

    net.start()
    api.start()
    osm1.start()
    print('osm1 up!')
    osm2.start()
    print('osm2 up!')

    vim_id1 = osm1.register_emulated_api('vim', api)
    osm1.onboard_vnfd('vnfs/ping_vnf')
    osm1.onboard_vnfd('vnfs/pong_vnf')
    nsd_id1 = osm1.onboard_nsd('services/pingpong_ns')
    ns_id1 = osm1.ns_create('pingpong-test1', nsd_id1, vim_id1)

    vim_id2 = osm2.register_emulated_api('vim', api)
    osm2.onboard_vnfd('vnfs/ping_vnf')
    osm2.onboard_vnfd('vnfs/pong_vnf')
    nsd_id2 = osm2.onboard_nsd('services/pingpong_ns')
    ns_id2 = osm2.ns_create('pingpong-test2', nsd_id2, vim_id2)

    osm1.ns_wait_until_all_in_status('running')
    osm2.ns_wait_until_all_in_status('running')
    print('all ready!')

    osm1.ns_delete(ns_id1)
    osm2.ns_delete(ns_id2)

    osm1.ns_wait_until_all_in_status('terminated')
    osm2.ns_wait_until_all_in_status('terminated')
    print('all deleted!')

finally:
    api.stop()
    net.stop()
