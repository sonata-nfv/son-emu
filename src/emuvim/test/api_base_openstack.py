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
import unittest
import os
import subprocess
import docker
import time
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from mininet.clean import cleanup
from mininet.node import Controller


class ApiBaseOpenStack(unittest.TestCase):
    """
        Helper class to do basic test setups.
        s1 -- s2 -- s3 -- ... -- sN
    """

    def __init__(self, *args, **kwargs):
        self.net = None
        self.api = []
        self.s = []   # list of switches
        self.h = []   # list of hosts
        self.d = []   # list of docker containers
        self.dc = []  # list of data centers
        self.docker_cli = None
        super(ApiBaseOpenStack, self).__init__(*args, **kwargs)

    def createNet(
            self,
            nswitches=0, ndatacenter=0, nhosts=0, ndockers=0,
            autolinkswitches=False, controller=Controller, **kwargs):
        """
        Creates a Mininet instance and automatically adds some
        nodes to it.

        Attention, we should always use Mininet's default controller
        for our tests. Only use other controllers if you want to test
        specific controller functionality.
        """
        self.net = DCNetwork(controller=controller, **kwargs)
        for i in range(0, ndatacenter):
            self.api.append(OpenstackApiEndpoint("0.0.0.0", 15000 + i))

        # add some switches
        # start from s1 because ovs does not like to have dpid = 0
        # and switch name-number is being used by mininet to set the dpid
        for i in range(1, nswitches + 1):
            self.s.append(self.net.addSwitch('s%d' % i))
        # if specified, chain all switches
        if autolinkswitches:
            for i in range(0, len(self.s) - 1):
                self.net.addLink(self.s[i], self.s[i + 1])
            # link switches s1, s2 and s3
            self.net.addLink(self.s[2], self.s[0])

        # add some data centers
        for i in range(0, ndatacenter):
            self.dc.append(
                self.net.addDatacenter(
                    'dc%d' % i,
                    metadata={"unittest_dc": i}))
        # link switches dc0.s1 with s1
        self.net.addLink(self.dc[0].switch, self.s[0])
        # connect data centers to the endpoint
        for i in range(0, ndatacenter):
            self.api[i].connect_datacenter(self.dc[i])
            self.api[i].connect_dc_network(self.net)
        # add some hosts
        for i in range(0, nhosts):
            self.h.append(self.net.addHost('h%d' % i))
        # add some dockers
        for i in range(0, ndockers):
            self.d.append(self.net.addDocker('d%d' %
                                             i, dimage="ubuntu:trusty"))

    def startApi(self):
        for i in self.api:
            i.start(wait_for_port=True)

    def stopApi(self):
        for i in self.api:
            i.manage.stop_floating_network()
            i.stop()

    def startNet(self):
        self.net.start()

    def stopNet(self):
        self.net.stop()

    def getDockerCli(self):
        """
        Helper to interact with local docker instance.
        """
        if self.docker_cli is None:
            self.docker_cli = docker.Client(
                base_url='unix://var/run/docker.sock')
        return self.docker_cli

    def getContainernetContainers(self):
        """
        List the containers managed by containernet
        """
        return self.getDockerCli().containers(
            filters={"label": "com.containernet"})

    @staticmethod
    def setUp():
        pass

    def tearDown(self):
        time.sleep(2)
        print('->>>>>>> tear everything down ->>>>>>>>>>>>>>>')
        self.stopApi()  # stop all flask threads
        self.stopNet()  # stop some mininet and containernet stuff
        cleanup()
        # make sure that all pending docker containers are killed
        # kill a possibly running docker process that blocks the open ports
        with open(os.devnull, 'w') as devnull:
            subprocess.call("kill $(netstat -npl | grep '15000' | grep -o -e'[0-9]\+/docker' | grep -o -e '[0-9]\+')",
                            stdout=devnull,
                            stderr=devnull,
                            shell=True)

        with open(os.devnull, 'w') as devnull:
            subprocess.call(
                "sudo docker rm -f $(sudo docker ps --filter 'label=com.containernet' -a -q)",
                stdout=devnull,
                stderr=devnull,
                shell=True)
        time.sleep(2)
