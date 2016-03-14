"""
Test suite to automatically test emulator functionalities.
Directly interacts with the emulator through the Mininet-like
Python API.

Does not test API endpoints. This is done in separated test suites.
"""

import time
import unittest
from emuvim.dcemulator.node import EmulatorCompute
from emuvim.test.base import SimpleTestTopology


#@unittest.skip("disabled topology tests for development")
class testEmulatorTopology( SimpleTestTopology ):
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
        time.sleep(5)
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
        time.sleep(5)
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


#@unittest.skip("disabled compute tests for development")
class testEmulatorCompute( SimpleTestTopology ):
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
