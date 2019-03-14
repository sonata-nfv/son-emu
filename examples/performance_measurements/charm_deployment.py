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
import logging
import os
import subprocess

import shutil
import time

from emuvim.api.osm.pre_configured_osm import PreConfiguredOSM
from emuvim.api.util.docker_utils import build_dockerfile_dir
from mininet.log import setLogLevel

logging.basicConfig(level=logging.DEBUG)
setLogLevel('debug')  # set Mininet loglevel
logging.getLogger('werkzeug').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.base').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.compute').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.keystone').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.nova').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.neutron').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.heat').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.heat.parser').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.glance').setLevel(logging.DEBUG)
logging.getLogger('api.openstack.helper').setLevel(logging.DEBUG)

prefix = os.path.dirname(os.path.abspath(__file__))

build_dockerfile_dir('../images/sshcontainer/', 'sshcontainer')

layers_folder = os.path.join(prefix, '../charms/layers')
simple_charm_folder = os.path.join(layers_folder, 'simple')
charm_target_dir = os.path.join(prefix, '../vnfs/simple_charmed_vnfd/charms/')
shutil.rmtree(charm_target_dir, ignore_errors=True)
if not subprocess.call(['/snap/bin/charm', 'build'], cwd=simple_charm_folder, env={
    'CHARM_BUILD_DIR': charm_target_dir,
    'CHARM_LAYERS_DIR': layers_folder
}) in [0, 100]:  # 100 means tests skipped
    raise RuntimeError('charm build failed')


def get_detailed_configuration_status(osm):
    status = osm.ns_get(ns_id)['_admin']['deployed']['VCA'][0]['detailed-status']
    print('current status: %s' % status)
    return status


def wait_for_detailed_configuration_status(osm, status):
    while get_detailed_configuration_status(osm) != status:
        time.sleep(1)


with open('charmed-%d.csv' % time.time(), 'w') as csvfile:
    fieldnames = ['ns_create', 'charm_deployment_start', 'waiting_for_machine', 'installing_charm_software',
                  'ns_action', 'ns_delete']
    writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
    writer.writeheader()

    for n in range(1, 10 + 1):
        with PreConfiguredOSM() as osm:
            osm.onboard_vnfd('../vnfs/simple_charmed_vnfd')
            nsd_id = osm.onboard_nsd('../services/simple_charmed_nsd')
            ns_create = time.time()
            ns_id = osm.ns_create('charmed-ns-%d' % n, nsd_id)
            osm.ns_wait_until_all_in_status('running')
            ns_created = time.time()

            wait_for_detailed_configuration_status(osm, 'waiting for machine')
            waiting_for_machine_start = time.time()

            wait_for_detailed_configuration_status(osm, 'installing charm software')
            installing_charm_start = time.time()

            wait_for_detailed_configuration_status(osm, 'Ready!')
            ready = time.time()

            instance = osm.api.compute.find_server_by_name_or_id('dc1_charmed-ns-%d-1--1' % n).emulator_compute
            osm.ns_action(ns_id, 1, 'touch')
            while instance.cmd('cat /testmanual') != '':
                time.sleep(0.1)
            ns_action_done = time.time()

            osm.ns_delete(ns_id)
            osm.ns_wait_until_all_in_status('terminated')
            ns_deleted = time.time()

            writer.writerow({
                'ns_create': ns_created - ns_create,
                'charm_deployment_start': waiting_for_machine_start - ns_created,
                'waiting_for_machine': installing_charm_start - waiting_for_machine_start,
                'installing_charm_software': ready - installing_charm_start,
                'ns_action': ns_action_done - ready,
                'ns_delete': ns_deleted - ns_action_done,
            })
            csvfile.flush()
