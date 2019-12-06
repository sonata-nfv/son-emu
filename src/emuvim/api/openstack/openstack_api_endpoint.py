# Copyright (c) 2015 SONATA-NFV and Paderborn University
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
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
from emuvim.api.openstack.manage import OpenstackManage

from emuvim.api.openstack.openstack_dummies.glance_dummy_api import \
    GlanceDummyApi
from emuvim.api.openstack.openstack_dummies.heat_dummy_api import \
    HeatDummyApi
from emuvim.api.openstack.openstack_dummies.keystone_dummy_api import \
    KeystoneDummyApi
from emuvim.api.openstack.openstack_dummies.neutron_dummy_api import \
    NeutronDummyApi
from emuvim.api.openstack.openstack_dummies.nova_dummy_api import \
    NovaDummyApi

import logging
import emuvim.api.openstack.compute as compute
import socket
import time


class OpenstackApiEndpoint():
    """
    Base class for an OpenStack datacenter.
    It holds information about all connected endpoints.
    """
    dc_apis = []

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.compute = compute.OpenstackCompute()
        self.openstack_endpoints = dict()
        self.openstack_endpoints['keystone'] = KeystoneDummyApi(
            self.ip, self.port)
        self.openstack_endpoints['neutron'] = NeutronDummyApi(
            self.ip, self.port + 4696, self.compute)
        self.openstack_endpoints['nova'] = NovaDummyApi(
            self.ip, self.port + 3774, self.compute)
        self.openstack_endpoints['heat'] = HeatDummyApi(
            self.ip, self.port + 3004, self.compute)
        self.openstack_endpoints['glance'] = GlanceDummyApi(
            self.ip, self.port + 4242, self.compute)

        self.rest_threads = list()
        self.manage = OpenstackManage()
        self.manage.add_endpoint(self)
        OpenstackApiEndpoint.dc_apis.append(self)

    def connect_datacenter(self, dc):
        """
        Connect a datacenter to this endpoint.
        An endpoint can only be connected to a single datacenter.

        :param dc: Datacenter object
        :type dc: :class:`dc`
        """
        self.compute.dc = dc
        for ep in self.openstack_endpoints.values():
            ep.manage = self.manage
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" %
                     (dc.label, self.__class__.__name__, self.ip, self.port))

    def connect_dc_network(self, dc_network):
        """
        Connect the datacenter network to the endpoint.

        :param dc_network: Datacenter network reference
        :type dc_network: :class:`.net`
        """
        self.manage.net = dc_network
        self.compute.nets[self.manage.floating_network.id] = self.manage.floating_network
        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self, wait_for_port=False):
        """
        Start all connected OpenStack endpoints that are connected to this API endpoint.
        """
        for c in self.openstack_endpoints.values():
            c.compute = self.compute
            c.manage = self.manage
            c.start()
            if wait_for_port:
                self._wait_for_port(c.ip, c.port)

    def stop(self):
        """
        Stop all connected OpenStack endpoints that are connected to this API endpoint.
        """
        for c in self.openstack_endpoints.values():
            c.stop()
        for c in self.openstack_endpoints.values():
            if c.server_thread:
                c.server_thread.join()
        self.manage.stop()

    def _wait_for_port(self, ip, port):
        for i in range(0, 10):
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1)  # 1 Second Timeout
            r = s.connect_ex((ip, port))
            if r == 0:
                break  # port is open proceed
            else:
                logging.warning(
                    "Waiting for {}:{} ... ({}/10)".format(ip, port, i + 1))
            time.sleep(1)
