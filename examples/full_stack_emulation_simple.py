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

from emuvim.api.osm.pre_configured_osm import PreConfiguredOSM

from mininet.log import setLogLevel
setLogLevel('debug')

with PreConfiguredOSM() as osm:
    osm.onboard_vnfd('vnfs/ping_vnf')
    osm.onboard_vnfd('vnfs/pong_vnf')
    nsd_id = osm.onboard_nsd('services/pingpong_ns')
    ns_id = osm.ns_create('pingpong-test', nsd_id)

    osm.ns_wait_until_all_in_status('running')
    osm.ns_delete(ns_id)
    osm.ns_wait_until_all_in_status('terminated')
