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
import logging
import time
import signal
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from mininet.link import TCLink

logging.basicConfig(level=logging.INFO)
setLogLevel('info')  # set Mininet loglevel
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


class DaemonTopology(object):
    """
    Topology with two datacenters:

        dc1 <-- 50ms --> dc2
    """

    def __init__(self):
        self.running = True
        signal.signal(signal.SIGINT, self._stop_by_signal)
        signal.signal(signal.SIGTERM, self._stop_by_signal)
        # create and start topology
        self.create_topology()
        self.start_topology()
        self.daemonize()
        self.stop_topology()

    def create_topology(self):
        self.net = DCNetwork(monitor=False, enable_learning=True)
        self.dc1 = self.net.addDatacenter("dc1")
        self.dc2 = self.net.addDatacenter("dc2")
        self.net.addLink(self.dc1, self.dc2, cls=TCLink, delay="50ms")
        # add OpenStack-like APIs to the emulated DC
        self.api1 = OpenstackApiEndpoint("0.0.0.0", 6001)
        self.api1.connect_datacenter(self.dc1)
        self.api1.connect_dc_network(self.net)
        self.api2 = OpenstackApiEndpoint("0.0.0.0", 6002)
        self.api2.connect_datacenter(self.dc2)
        self.api2.connect_dc_network(self.net)
        # add the command line interface endpoint to the emulated DC (REST API)
        self.rapi1 = RestApiEndpoint("0.0.0.0", 5001)
        self.rapi1.connectDCNetwork(self.net)
        self.rapi1.connectDatacenter(self.dc1)
        self.rapi1.connectDatacenter(self.dc2)

    def start_topology(self):
        self.api1.start()
        self.api2.start()
        self.rapi1.start()
        self.net.start()

    def daemonize(self):
        print("Daemonizing vim-emu. Send SIGTERM or SIGKILL to stop.")
        while self.running:
            time.sleep(1)

    def _stop_by_signal(self, signum, frame):
        print("Received SIGNAL {}. Stopping.".format(signum))
        self.running = False

    def stop_topology(self):
        self.api1.stop()
        self.api2.stop()
        self.rapi1.stop()
        self.net.stop()


def main():
    DaemonTopology()


if __name__ == '__main__':
    main()
