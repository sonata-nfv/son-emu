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

import psutil

from emuvim.api.osm.pre_configured_osm import PreConfiguredOSM

import csv


with open('limit_testing_%d.csv' % time.time(), 'w') as csvfile:
    fieldnames = ['i', 'used_ram', 'cpu_usage']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    start = time.time()
    with PreConfiguredOSM() as osm:
        start_done = time.time()
        osm.onboard_vnfd('../vnfs/multiple_vdu_vnfd')
        nsd_id = osm.onboard_nsd('../services/multiple_vdu_nsd')

        i = 0
        while True:
            time.sleep(3)

            measurement = {
                'i': i,
                'used_ram': psutil.virtual_memory().used,
                'cpu_usage': psutil.cpu_percent(interval=1)
            }
            writer.writerow(measurement)
            csvfile.flush()

            i += 1

            osm.ns_create('multiple-vdu-test-%d' % i, nsd_id)
            _, num_failed = osm.ns_wait_until_all_in_status('running', 'failed')
            if num_failed != 0:
                print('NS failed')
                break

        for ns in osm.ns_list():
            osm.ns_delete(ns['id'])

        osm.ns_wait_until_all_in_status('terminated')
