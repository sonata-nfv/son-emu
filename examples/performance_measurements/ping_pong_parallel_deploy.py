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

import time

from emuvim.api.osm.pre_configured_osm import PreConfiguredOSM

import csv


with open('ping_pong_parallel_deploy_and_delete_%d.csv' % time.time(), 'w') as csvfile:
    fieldnames = ['n', 'start', 'onboard', 'ns_start', 'num_failed', 'ns_delete', 'stop']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    MAX = 30

    for n in range(0, MAX + 1, 1):
        start = time.time()
        with PreConfiguredOSM() as osm:
            start_done = time.time()
            osm.onboard_vnfd('../vnfs/ping_vnf')
            osm.onboard_vnfd('../vnfs/pong_vnf')
            nsd_id = osm.onboard_nsd('../services/pingpong_ns')
            onboard_done = time.time()
            for i in range(n):
                osm.ns_create('pingpong-test-%d' % i, nsd_id)

            _, num_failed = osm.ns_wait_until_all_in_status('running', 'failed')

            ns_start_done = time.time()

            for ns in osm.ns_list():
                osm.ns_delete(ns['id'])

            osm.ns_wait_until_all_in_status('terminated')

            ns_delete_done = time.time()
        stop_done = time.time()

        measurement = {
            'n': n,
            'start': start_done - start,
            'onboard': onboard_done - start_done,
            'ns_start': ns_start_done - onboard_done,
            'num_failed': num_failed,
            'ns_delete': ns_delete_done - ns_start_done,
            'stop': stop_done - ns_delete_done,
        }
        writer.writerow(measurement)
        csvfile.flush()
