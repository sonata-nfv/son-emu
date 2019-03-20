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
from emuvim.dcemulator.net import DCNetwork
from mininet.clean import cleanup
from mininet.node import Controller


class SimpleTestTopology(unittest.TestCase):
    """
        Helper class to do basic test setups.
        s1 -- s2 -- s3 -- ... -- sN
    """

    def __init__(self, *args, **kwargs):
        self.net = None
        self.s = []   # list of switches
        self.h = []   # list of hosts
        self.d = []   # list of docker containers
        self.dc = []  # list of data centers
        self.docker_cli = None
        super(SimpleTestTopology, self).__init__(*args, **kwargs)

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

        # add some switches
        # start from s1 because ovs does not like to have dpid = 0
        # and switch name-number is being used by mininet to set the dpid
        for i in range(1, nswitches + 1):
            self.s.append(self.net.addSwitch('s%d' % i))
        # if specified, chain all switches
        if autolinkswitches:
            for i in range(0, len(self.s) - 1):
                self.net.addLink(self.s[i], self.s[i + 1])
        # add some data centers
        for i in range(0, ndatacenter):
            self.dc.append(
                self.net.addDatacenter(
                    'datacenter%d' % i,
                    metadata={"unittest_dc": i}))
        # add some hosts
        for i in range(0, nhosts):
            self.h.append(self.net.addHost('h%d' % i))
        # add some dockers
        for i in range(0, ndockers):
            self.d.append(self.net.addDocker('d%d' %
                                             i, dimage="ubuntu:trusty"))

    def startNet(self):
        self.net.start()

    def stopNet(self):
        self.net.stop()

    def getDockerCli(self):
        """
        Helper to interact with local docker instance.
        """
        if self.docker_cli is None:
            self.docker_cli = docker.APIClient(
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

    @staticmethod
    def tearDown():
        cleanup()
        # make sure that all pending docker containers are killed
        with open(os.devnull, 'w') as devnull:
            subprocess.call(
                "sudo docker rm -f $(sudo docker ps --filter 'label=com.containernet' -a -q)",
                stdout=devnull,
                stderr=devnull,
                shell=True)
