"""
Test suite to automatically test emulator functionalities.
Directly interacts with the emulator through the Mininet-like
Python API.

Does not test API endpoints. This is done in separated test suites.
"""

import unittest
import os
import time
import subprocess
import docker
from dcemulator.net import DCNetwork
from dcemulator.node import EmulatorCompute
from mininet.node import Host, Controller, OVSSwitch, Docker
from mininet.link import TCLink
from mininet.topo import SingleSwitchTopo, LinearTopo
from mininet.log import setLogLevel
from mininet.util import quietRun
from mininet.clean import cleanup


class simpleTestTopology( unittest.TestCase ):
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
        super(simpleTestTopology, self).__init__(*args, **kwargs)

    def createNet(
            self,
            nswitches=0, ndatacenter=0, nhosts=0, ndockers=0,
            autolinkswitches=False):
        """
        Creates a Mininet instance and automatically adds some
        nodes to it.
        """
        self.net = net = DCNetwork()

        # add some switches
        for i in range(0, nswitches):
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
            self.d.append(self.net.addDocker('d%d' % i, dimage="ubuntu"))

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

    def getDockernetContainers(self):
        """
        List the containers managed by dockernet
        """
        return self.getDockerCli().containers(filters={"label": "com.dockernet"})

    @staticmethod
    def setUp():
        pass

    @staticmethod
    def tearDown():
        cleanup()
        # make sure that all pending docker containers are killed
        with open(os.devnull, 'w') as devnull:
            subprocess.call(
                "sudo docker rm -f $(sudo docker ps --filter 'label=com.dockernet' -a -q)",
                stdout=devnull,
                stderr=devnull,
                shell=True)


#@unittest.skip("disabled topology tests for development")
class testEmulatorTopology( simpleTestTopology ):
    """
    Tests to check the topology API of the emulator.
    """

    def testSingleDatacenter(self):
        """
        Create a single data center and add check if its switch is up
        by using manually added hosts. Tests especially the
        data center specific addLink method.
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=1, nhosts=2, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[0])
        # start Mininet network
        self.startNet()
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 0)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 1)
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    def testMultipleDatacenterDirect(self):
        """
        Create a two data centers and interconnect them.
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=2, nhosts=2, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[1])
        self.net.addLink(self.dc[0], self.dc[1])
        # start Mininet network
        self.startNet()
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 0)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 2)
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    def testMultipleDatacenterWithIntermediateSwitches(self):
        """
        Create a two data centers and interconnect them with additional
        switches between them.
        """
        # create network
        self.createNet(
            nswitches=3, ndatacenter=2, nhosts=2, ndockers=0,
            autolinkswitches=True)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[1])
        self.net.addLink(self.dc[0], self.s[0])
        self.net.addLink(self.s[2], self.dc[1])
        # start Mininet network
        self.startNet()
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 0)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 5)
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


#@unittest.skip("disabled compute tests for development")
class testEmulatorCompute( simpleTestTopology ):
    """
    Tests to check the emulator's API to add and remove
    compute resources at runtime.
    """

    def testAddSingleComputeSingleDC(self):
        """
        Adds a single compute instance to
        a single DC and checks its connectivity with a
        manually added host.
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=1, nhosts=1, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        # start Mininet network
        self.startNet()
        # add compute resources
        vnf1 = self.dc[0].startCompute("vnf1")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 1)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 1)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 1)
        assert(isinstance(self.dc[0].listCompute()[0], EmulatorCompute))
        assert(self.dc[0].listCompute()[0].name == "vnf1")
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], vnf1]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    def testRemoveSingleComputeSingleDC(self):
        """
        Test stop method for compute instances.
        Check that the instance is really removed.
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=1, nhosts=1, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        # start Mininet network
        self.startNet()
        # add compute resources
        vnf1 = self.dc[0].startCompute("vnf1")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 1)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 1)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 1)
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], vnf1]) <= 0.0)
        # remove compute resources
        self.dc[0].stopCompute("vnf1")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 0)
        assert(len(self.net.hosts) == 1)
        assert(len(self.net.switches) == 1)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 0)
        # stop Mininet network
        self.stopNet()

    def testGetStatusSingleComputeSingleDC(self):
        """
        Check if the getStatus functionality of EmulatorCompute
        objects works well.
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=1, nhosts=1, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        # start Mininet network
        self.startNet()
        # add compute resources
        vnf1 = self.dc[0].startCompute("vnf1")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 1)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 1)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 1)
        assert(isinstance(self.dc[0].listCompute()[0], EmulatorCompute))
        assert(self.dc[0].listCompute()[0].name == "vnf1")
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], vnf1]) <= 0.0)
        # check get status
        s = self.dc[0].containers.get("vnf1").getStatus()
        assert(s["name"] == "vnf1")
        assert(s["state"]["Running"])
        # stop Mininet network
        self.stopNet()

    def testConnectivityMultiDC(self):
        """
        Test if compute instances started in different data centers
        are able to talk to each other.
        """
        # create network
        self.createNet(
            nswitches=3, ndatacenter=2, nhosts=0, ndockers=0,
            autolinkswitches=True)
        # setup links
        self.net.addLink(self.dc[0], self.s[0])
        self.net.addLink(self.dc[1], self.s[2])
        # start Mininet network
        self.startNet()
        # add compute resources
        vnf1 = self.dc[0].startCompute("vnf1")
        vnf2 = self.dc[1].startCompute("vnf2")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 2)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 5)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 1)
        assert(len(self.dc[1].listCompute()) == 1)
        # check connectivity by using ping
        assert(self.net.ping([vnf1, vnf2]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    def testInterleavedAddRemoveMultiDC(self):
        """
        Test multiple, interleaved add and remove operations and ensure
        that always all expected compute instances are reachable.
        """
                # create network
        self.createNet(
            nswitches=3, ndatacenter=2, nhosts=0, ndockers=0,
            autolinkswitches=True)
        # setup links
        self.net.addLink(self.dc[0], self.s[0])
        self.net.addLink(self.dc[1], self.s[2])
        # start Mininet network
        self.startNet()
        # add compute resources
        vnf1 = self.dc[0].startCompute("vnf1")
        vnf2 = self.dc[1].startCompute("vnf2")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 2)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 5)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 1)
        assert(len(self.dc[1].listCompute()) == 1)
        # check connectivity by using ping
        assert(self.net.ping([vnf1, vnf2]) <= 0.0)
        # remove compute resources
        self.dc[0].stopCompute("vnf1")
        # check number of running nodes
        assert(len(self.getDockernetContainers()) == 1)
        assert(len(self.net.hosts) == 1)
        assert(len(self.net.switches) == 5)
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 0)
        assert(len(self.dc[1].listCompute()) == 1)
        # add compute resources
        vnf3 = self.dc[0].startCompute("vnf3")
        vnf4 = self.dc[0].startCompute("vnf4")
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 2)
        assert(len(self.dc[1].listCompute()) == 1)
        assert(self.net.ping([vnf3, vnf2]) <= 0.0)
        assert(self.net.ping([vnf4, vnf2]) <= 0.0)
        # remove compute resources
        self.dc[0].stopCompute("vnf3")
        self.dc[0].stopCompute("vnf4")
        self.dc[1].stopCompute("vnf2")
        # check compute list result
        assert(len(self.dc[0].listCompute()) == 0)
        assert(len(self.dc[1].listCompute()) == 0)
        # stop Mininet network
        self.stopNet()

if __name__ == '__main__':
    unittest.main()
