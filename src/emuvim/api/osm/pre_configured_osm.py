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

from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from emuvim.api.osm.osm import OSM
from emuvim.dcemulator.net import DCNetwork


class PreConfiguredOSM:
    def __init__(self,
                 vca_host=os.environ.get('VCA_HOST'),
                 vca_secret=os.environ.get('VCA_SECRET'),
                 osm_version='releasefive-daily'):
        self.net = DCNetwork(monitor=False, enable_learning=True)
        dc1 = self.net.addDatacenter("dc1")
        self.api = OpenstackApiEndpoint("0.0.0.0", 6001)
        self.api.connect_datacenter(dc1)
        self.api.connect_dc_network(self.net)

        s1 = self.net.addSwitch('s1')
        self.osm = OSM(self.net, s1, vca_host=vca_host, vca_secret=vca_secret, osm_version=osm_version)
        self.vim_emu_id = None

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.stop()

    def start(self):
        self.net.start()
        self.api.start()
        self.osm.start()
        self.vim_emu_id = self.osm.register_emulated_api('emu-vim1', self.api)

    def stop(self):
        self.api.stop()
        self.net.stop()

    def ns_create(self, ns_name, nsd_id):
        return self.osm.ns_create(ns_name, nsd_id, self.vim_emu_id)

    # forward api related calls
    def onboard_vnfd(self, *args, **kwargs):
        return self.osm.onboard_vnfd(*args, **kwargs)

    def onboard_nsd(self, *args, **kwargs):
        return self.osm.onboard_nsd(*args, **kwargs)

    def ns_list(self):
        return self.osm.ns_list()

    def ns_delete(self, *args, **kwargs):
        return self.osm.ns_delete(*args, **kwargs)

    def ns_get(self, *args, **kwargs):
        return self.osm.ns_get(*args, **kwargs)

    def ns_action(self, *args, **kwargs):
        return self.osm.ns_action(*args, **kwargs)

    def ns_wait_until_all_in_status(self, *args, **kwargs):
        return self.osm.ns_wait_until_all_in_status(*args, **kwargs)
