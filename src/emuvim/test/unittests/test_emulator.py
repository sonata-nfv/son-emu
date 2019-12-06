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
from emuvim.dcemulator.node import EmulatorCompute
from emuvim.test.base import SimpleTestTopology
from mininet.node import RemoteController


# @unittest.skip("disabled topology tests for development")
class testEmulatorTopology(SimpleTestTopology):
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
        self.assertTrue(len(self.getContainernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    # @unittest.skip("disabled to test if CI fails because this is the first test.")
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
        self.assertTrue(len(self.getContainernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 2)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
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
        self.assertTrue(len(self.getContainernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 5)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


class testEmulatorNetworking(SimpleTestTopology):

    def testSDNChainingSingleService_withLearning(self):
        """
        Create a two data centers and interconnect them with additional
        switches between them.
        Uses Ryu SDN controller.
        Connect the Docker hosts to different datacenters and setup the links between.
        """
        # create network
        self.createNet(
            nswitches=3, ndatacenter=2, nhosts=0, ndockers=0,
            autolinkswitches=True,
            controller=RemoteController,
            enable_learning=True)
        # setup links
        self.net.addLink(self.dc[0], self.s[0])
        self.net.addLink(self.s[2], self.dc[1])
        # start Mininet network
        self.startNet()

        # add compute resources
        vnf1 = self.dc[0].startCompute(
            "vnf1", network=[{'id': 'intf1', 'ip': '10.0.10.1/24'}])
        vnf2 = self.dc[1].startCompute(
            "vnf2", network=[{'id': 'intf2', 'ip': '10.0.10.2/24'}])
        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 2)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 5)
        # check status
        # check get status
        s1 = self.dc[0].containers.get("vnf1").getStatus()
        print(s1)
        self.assertTrue(s1["name"] == "vnf1")
        self.assertTrue(s1["state"]["Running"])
        self.assertTrue(s1["network"][0]['intf_name'] == 'intf1')
        self.assertTrue(s1["network"][0]['ip'] == '10.0.10.1/24')

        s2 = self.dc[1].containers.get("vnf2").getStatus()
        print(s2)
        self.assertTrue(s2["name"] == "vnf2")
        self.assertTrue(s2["state"]["Running"])
        self.assertTrue(s2["network"][0]['intf_name'] == 'intf2')
        self.assertTrue(s2["network"][0]['ip'] == '10.0.10.2/24')

        # should be connected because learning = True
        self.assertTrue(self.net.ping([vnf1, vnf2]) <= 0.0)
        # setup links
        self.net.setChain('vnf1', 'vnf2', 'intf1', 'intf2',
                          bidirectional=True, cmd='add-flow')
        # should still be connected
        self.assertTrue(self.net.ping([vnf1, vnf2]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    def testSDNChainingSingleService(self):
        """
        Create a two data centers and interconnect them with additional
        switches between them.
        Uses Ryu SDN controller.
        Connect the Docker hosts to different datacenters and setup the links between.
        """
        # create network
        self.createNet(
            nswitches=3, ndatacenter=2, nhosts=0, ndockers=0,
            autolinkswitches=True,
            controller=RemoteController,
            enable_learning=False)
        # setup links
        self.net.addLink(self.dc[0], self.s[0])
        self.net.addLink(self.s[2], self.dc[1])
        # start Mininet network
        self.startNet()

        # add compute resources
        vnf1 = self.dc[0].startCompute(
            "vnf1", network=[{'id': 'intf1', 'ip': '10.0.10.1/24'}])
        vnf2 = self.dc[1].startCompute(
            "vnf2", network=[{'id': 'intf2', 'ip': '10.0.10.2/24'}])
        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 2)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 5)
        # check status
        # check get status
        s1 = self.dc[0].containers.get("vnf1").getStatus()
        print(s1)
        self.assertTrue(s1["name"] == "vnf1")
        self.assertTrue(s1["state"]["Running"])
        self.assertTrue(s1["network"][0]['intf_name'] == 'intf1')
        self.assertTrue(s1["network"][0]['ip'] == '10.0.10.1/24')

        s2 = self.dc[1].containers.get("vnf2").getStatus()
        print(s2)
        self.assertTrue(s2["name"] == "vnf2")
        self.assertTrue(s2["state"]["Running"])
        self.assertTrue(s2["network"][0]['intf_name'] == 'intf2')
        self.assertTrue(s2["network"][0]['ip'] == '10.0.10.2/24')

        # should be not not yet connected
        self.assertTrue(self.net.ping([vnf1, vnf2]) > 0.0)
        # setup links
        self.net.setChain('vnf1', 'vnf2', 'intf1', 'intf2',
                          bidirectional=True, cmd='add-flow')
        # check connectivity by using ping
        self.assertTrue(self.net.ping([vnf1, vnf2]) <= 0.0)
        # stop Mininet network
        self.stopNet()

    def testSDNChainingMultiService(self):
        """
        Create a two data centers and interconnect them with additional
        switches between them.
        Uses Ryu SDN controller.
        Setup 2 services and setup isolated paths between them
        Delete only the first service, and check that other one still works
        """
        # create network
        self.createNet(
            nswitches=3, ndatacenter=2, nhosts=0, ndockers=0,
            autolinkswitches=True,
            controller=RemoteController,
            enable_learning=False)
        # setup links
        self.net.addLink(self.dc[0], self.s[0])
        self.net.addLink(self.s[2], self.dc[1])
        # start Mininet network
        self.startNet()

        # First Service
        # add compute resources
        vnf1 = self.dc[0].startCompute(
            "vnf1", network=[{'id': 'intf1', 'ip': '10.0.10.1/24'}])
        vnf2 = self.dc[1].startCompute(
            "vnf2", network=[{'id': 'intf2', 'ip': '10.0.10.2/24'}])
        # setup links
        self.net.setChain('vnf1', 'vnf2', 'intf1', 'intf2',
                          bidirectional=True, cmd='add-flow', cookie=1)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([vnf1, vnf2]) <= 0.0)

        # Second Service
        # add compute resources
        vnf11 = self.dc[0].startCompute(
            "vnf11", network=[{'id': 'intf1', 'ip': '10.0.20.1/24'}])
        vnf22 = self.dc[1].startCompute(
            "vnf22", network=[{'id': 'intf2', 'ip': '10.0.20.2/24'}])

        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 4)
        self.assertTrue(len(self.net.hosts) == 4)
        self.assertTrue(len(self.net.switches) == 5)

        # setup links
        self.net.setChain('vnf11', 'vnf22', 'intf1', 'intf2',
                          bidirectional=True, cmd='add-flow', cookie=2)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([vnf11, vnf22]) <= 0.0)
        # check first service cannot ping second service
        self.assertTrue(self.net.ping([vnf1, vnf22]) > 0.0)
        self.assertTrue(self.net.ping([vnf2, vnf11]) > 0.0)

        # delete the first service chain
        self.net.setChain('vnf1', 'vnf2', 'intf1', 'intf2',
                          bidirectional=True, cmd='del-flows', cookie=1)
        # check connectivity of first service is down
        self.assertTrue(self.net.ping([vnf1, vnf2]) > 0.0)
        # time.sleep(100)
        # check connectivity of second service is still up
        self.assertTrue(self.net.ping([vnf11, vnf22]) <= 0.0)

        # stop Mininet network
        self.stopNet()

# @unittest.skip("disabled compute tests for development")


class testEmulatorCompute(SimpleTestTopology):
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
        self.assertTrue(len(self.getContainernetContainers()) == 1)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        self.assertTrue(isinstance(
            self.dc[0].listCompute()[0], EmulatorCompute))
        self.assertTrue(self.dc[0].listCompute()[0].name == "vnf1")
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], vnf1]) <= 0.0)
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
        self.assertTrue(len(self.getContainernetContainers()) == 1)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], vnf1]) <= 0.0)
        # remove compute resources
        self.dc[0].stopCompute("vnf1")
        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 1)
        self.assertTrue(len(self.net.switches) == 1)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 0)
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
        self.assertTrue(len(self.getContainernetContainers()) == 1)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        self.assertTrue(isinstance(
            self.dc[0].listCompute()[0], EmulatorCompute))
        self.assertTrue(self.dc[0].listCompute()[0].name == "vnf1")
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], vnf1]) <= 0.0)
        # check get status
        s = self.dc[0].containers.get("vnf1").getStatus()
        self.assertTrue(s["name"] == "vnf1")
        self.assertTrue(s["state"]["Running"])
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
        self.assertTrue(len(self.getContainernetContainers()) == 2)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 5)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([vnf1, vnf2]) <= 0.0)
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
        self.assertTrue(len(self.getContainernetContainers()) == 2)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 5)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 1)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([vnf1, vnf2]) <= 0.0)
        # remove compute resources
        self.dc[0].stopCompute("vnf1")
        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 1)
        self.assertTrue(len(self.net.hosts) == 1)
        self.assertTrue(len(self.net.switches) == 5)
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 0)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)
        # add compute resources
        vnf3 = self.dc[0].startCompute("vnf3")
        vnf4 = self.dc[0].startCompute("vnf4")
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 2)
        self.assertTrue(len(self.dc[1].listCompute()) == 1)
        self.assertTrue(self.net.ping([vnf3, vnf2]) <= 0.0)
        self.assertTrue(self.net.ping([vnf4, vnf2]) <= 0.0)
        # remove compute resources
        self.dc[0].stopCompute("vnf3")
        self.dc[0].stopCompute("vnf4")
        self.dc[1].stopCompute("vnf2")
        # check compute list result
        self.assertTrue(len(self.dc[0].listCompute()) == 0)
        self.assertTrue(len(self.dc[1].listCompute()) == 0)
        # stop Mininet network
        self.stopNet()


if __name__ == '__main__':
    unittest.main()
