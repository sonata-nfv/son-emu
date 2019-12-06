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
import time
import os
import unittest
from emuvim.test.base import SimpleTestTopology
from emuvim.dcemulator.resourcemodel import BaseResourceModel, ResourceFlavor, NotEnoughResourcesAvailable, ResourceModelRegistrar
from emuvim.dcemulator.resourcemodel.upb.simple import UpbSimpleCloudDcRM, UpbOverprovisioningCloudDcRM, UpbDummyRM


class testResourceModel(SimpleTestTopology):
    """
    Test the general resource model API and functionality.
    """

    def testBaseResourceModelApi(self):
        """
        Tast bare API without real resource madel.
        :return:
        """
        r = BaseResourceModel()
        # check if default flavors are there
        self.assertTrue(len(r._flavors) == 5)
        # check addFlavor functionality
        f = ResourceFlavor("test", {"testmetric": 42})
        r.addFlavour(f)
        self.assertTrue("test" in r._flavors)
        self.assertTrue(r._flavors.get("test").get("testmetric") == 42)

    def testAddRmToDc(self):
        """
        Test is allocate/free is called when a RM is added to a DC.
        :return:
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=1, nhosts=2, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[0])
        # add resource model
        r = BaseResourceModel()
        self.dc[0].assignResourceModel(r)
        # start Mininet network
        self.startNet()
        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check resource model and resource model registrar
        self.assertTrue(self.dc[0]._resource_model is not None)
        self.assertTrue(len(self.net.rm_registrar.resource_models) == 1)

        # check if alloc was called during startCompute
        self.assertTrue(len(r._allocated_compute_instances) == 0)
        self.dc[0].startCompute("tc1")
        time.sleep(1)
        self.assertTrue(len(r._allocated_compute_instances) == 1)
        # check if free was called during stopCompute
        self.dc[0].stopCompute("tc1")
        self.assertTrue(len(r._allocated_compute_instances) == 0)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


def createDummyContainerObject(name, flavor):

    class DummyContainer(object):

        def __init__(self):
            # take defaukt values from son-emu
            self.resources = dict(
                cpu_period=-1,
                cpu_quota=-1,
                mem_limit=-1,
                memswap_limit=-1
            )
            # self.cpu_period = self.resources['cpu_period']
            # self.cpu_quota = self.resources['cpu_quota']
            # self.mem_limit = self.resources['mem_limit']
            # self.memswap_limit = self.resources['memswap_limit']

        def updateCpuLimit(self, cpu_period, cpu_quota):
            self.resources['cpu_period'] = cpu_period
            self.resources['cpu_quota'] = cpu_quota

        def updateMemoryLimit(self, mem_limit):
            self.resources['mem_limit'] = mem_limit

    d = DummyContainer()
    d.name = name
    d.flavor_name = flavor
    return d


class testUpbSimpleCloudDcRM(SimpleTestTopology):
    """
    Test the UpbSimpleCloudDc resource model.
    """

    def testAllocationComputations(self):
        """
        Test the allocation procedures and correct calculations.
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 100
        E_MEM = 512
        MAX_MU = 2048
        # create dummy resource model environment
        reg = ResourceModelRegistrar(
            dc_emulation_max_cpu=E_CPU, dc_emulation_max_mem=E_MEM)
        rm = UpbSimpleCloudDcRM(max_cu=MAX_CU, max_mu=MAX_MU)
        reg.register("test_dc", rm)

        c1 = createDummyContainerObject("c1", flavor="tiny")
        rm.allocate(c1)  # calculate allocation
        # validate compute result
        self.assertEqual(float(
            c1.resources['cpu_quota']) / c1.resources['cpu_period'], E_CPU / MAX_CU * 0.5)
        # validate memory result
        self.assertEqual(
            float(c1.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 32)

        c2 = createDummyContainerObject("c2", flavor="small")
        rm.allocate(c2)  # calculate allocation
        # validate compute result
        self.assertEqual(float(
            c2.resources['cpu_quota']) / c2.resources['cpu_period'], E_CPU / MAX_CU * 1)
        # validate memory result
        self.assertEqual(
            float(c2.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 128)

        c3 = createDummyContainerObject("c3", flavor="medium")
        rm.allocate(c3)  # calculate allocation
        # validate compute result
        self.assertEqual(float(
            c3.resources['cpu_quota']) / c3.resources['cpu_period'], E_CPU / MAX_CU * 4)
        # validate memory result
        self.assertEqual(
            float(c3.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 256)

        c4 = createDummyContainerObject("c4", flavor="large")
        rm.allocate(c4)  # calculate allocation
        # validate compute result
        self.assertEqual(float(
            c4.resources['cpu_quota']) / c4.resources['cpu_period'], E_CPU / MAX_CU * 8)
        # validate memory result
        self.assertEqual(
            float(c4.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 512)

        c5 = createDummyContainerObject("c5", flavor="xlarge")
        rm.allocate(c5)  # calculate allocation
        # validate compute result
        self.assertEqual(float(
            c5.resources['cpu_quota']) / c5.resources['cpu_period'], E_CPU / MAX_CU * 16)
        # validate memory result
        self.assertEqual(
            float(c5.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 1024)

    def testAllocationCpuLimit(self):
        """
        Test CPU allocation limit
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 40
        E_MEM = 512
        MAX_MU = 4096
        # create dummy resource model environment
        reg = ResourceModelRegistrar(
            dc_emulation_max_cpu=E_CPU, dc_emulation_max_mem=E_MEM)
        rm = UpbSimpleCloudDcRM(max_cu=MAX_CU, max_mu=MAX_MU)
        reg.register("test_dc", rm)

        # test over provisioning exeption
        exception = False
        try:
            c6 = createDummyContainerObject("c6", flavor="xlarge")
            c7 = createDummyContainerObject("c7", flavor="xlarge")
            c8 = createDummyContainerObject("c8", flavor="xlarge")
            c9 = createDummyContainerObject("c9", flavor="xlarge")
            rm.allocate(c6)  # calculate allocation
            rm.allocate(c7)  # calculate allocation
            rm.allocate(c8)  # calculate allocation
            rm.allocate(c9)  # calculate allocation
        except NotEnoughResourcesAvailable as e:
            self.assertIn("Not enough compute", str(e))
            exception = True
        self.assertTrue(exception)

    def testAllocationMemLimit(self):
        """
        Test MEM allocation limit
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 500
        E_MEM = 512
        MAX_MU = 2048
        # create dummy resource model environment
        reg = ResourceModelRegistrar(
            dc_emulation_max_cpu=E_CPU, dc_emulation_max_mem=E_MEM)
        rm = UpbSimpleCloudDcRM(max_cu=MAX_CU, max_mu=MAX_MU)
        reg.register("test_dc", rm)

        # test over provisioning exeption
        exception = False
        try:
            c6 = createDummyContainerObject("c6", flavor="xlarge")
            c7 = createDummyContainerObject("c7", flavor="xlarge")
            c8 = createDummyContainerObject("c8", flavor="xlarge")
            rm.allocate(c6)  # calculate allocation
            rm.allocate(c7)  # calculate allocation
            rm.allocate(c8)  # calculate allocation
        except NotEnoughResourcesAvailable as e:
            self.assertIn("Not enough memory", str(e))
            exception = True
        self.assertTrue(exception)

    def testFree(self):
        """
        Test the free procedure.
        :return:
        """
        # create dummy resource model environment
        reg = ResourceModelRegistrar(
            dc_emulation_max_cpu=1.0, dc_emulation_max_mem=512)
        rm = UpbSimpleCloudDcRM(max_cu=100, max_mu=100)
        reg.register("test_dc", rm)
        c1 = createDummyContainerObject("c6", flavor="tiny")
        rm.allocate(c1)  # calculate allocation
        self.assertTrue(rm.dc_alloc_cu == 0.5)
        rm.free(c1)
        self.assertTrue(rm.dc_alloc_cu == 0)

    @unittest.skipIf(os.environ.get("SON_EMU_IN_DOCKER") is not None,
                     "skipping test when running inside Docker container")
    def testInRealTopo(self):
        """
        Start a real container and check if limitations are really passed down to Conteinernet.
        :return:
        """
        # create network
        self.createNet(nswitches=0, ndatacenter=1, nhosts=2, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[0])
        # add resource model
        r = UpbSimpleCloudDcRM(max_cu=100, max_mu=100)
        self.dc[0].assignResourceModel(r)
        # start Mininet network
        self.startNet()
        # check number of running nodes
        self.assertTrue(len(self.getContainernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check resource model and resource model registrar
        self.assertTrue(self.dc[0]._resource_model is not None)
        self.assertTrue(len(self.net.rm_registrar.resource_models) == 1)

        # check if alloc was called during startCompute
        self.assertTrue(len(r._allocated_compute_instances) == 0)
        tc1 = self.dc[0].startCompute("tc1", flavor_name="tiny")
        time.sleep(1)
        self.assertTrue(len(r._allocated_compute_instances) == 1)

        # check if there is a real limitation set for containers cgroup
        # deactivated for now, seems not to work in docker-in-docker setup used
        # in CI
        self.assertEqual(
            float(tc1.resources['cpu_quota']) / tc1.resources['cpu_period'], 0.005)

        # check if free was called during stopCompute
        self.dc[0].stopCompute("tc1")
        self.assertTrue(len(r._allocated_compute_instances) == 0)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


class testUpbOverprovisioningCloudDcRM(SimpleTestTopology):
    """
    Test the UpbOverprovisioningCloudDc resource model.
    """

    def testAllocationComputations(self):
        """
        Test the allocation procedures and correct calculations.
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 3
        E_MEM = 512
        MAX_MU = 2048
        # create dummy resource model environment
        reg = ResourceModelRegistrar(
            dc_emulation_max_cpu=E_CPU, dc_emulation_max_mem=E_MEM)
        rm = UpbOverprovisioningCloudDcRM(max_cu=MAX_CU, max_mu=MAX_MU)
        reg.register("test_dc", rm)

        c1 = createDummyContainerObject("c1", flavor="small")
        rm.allocate(c1)  # calculate allocation
        self.assertAlmostEqual(float(
            c1.resources['cpu_quota']) / c1.resources['cpu_period'], E_CPU / MAX_CU * 1.0, places=5)
        self.assertAlmostEqual(
            float(c1.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 128)
        self.assertAlmostEqual(rm.cpu_op_factor, 1.0)

        c2 = createDummyContainerObject("c2", flavor="small")
        rm.allocate(c2)  # calculate allocation
        self.assertAlmostEqual(float(
            c2.resources['cpu_quota']) / c2.resources['cpu_period'], E_CPU / MAX_CU * 1.0, places=5)
        self.assertAlmostEqual(
            float(c2.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 128)
        self.assertAlmostEqual(rm.cpu_op_factor, 1.0)

        c3 = createDummyContainerObject("c3", flavor="small")
        rm.allocate(c3)  # calculate allocation
        self.assertAlmostEqual(float(
            c3.resources['cpu_quota']) / c3.resources['cpu_period'], E_CPU / MAX_CU * 1.0, places=5)
        self.assertAlmostEqual(
            float(c3.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 128)
        self.assertAlmostEqual(rm.cpu_op_factor, 1.0)

        # from this container onwards, we should go to over provisioning mode:
        c4 = createDummyContainerObject("c4", flavor="small")
        rm.allocate(c4)  # calculate allocation
        self.assertAlmostEqual(float(
            c4.resources['cpu_quota']) / c4.resources['cpu_period'], E_CPU / MAX_CU * (float(3) / 4), places=5)
        self.assertAlmostEqual(float(
            c4.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 128, places=5)
        self.assertAlmostEqual(rm.cpu_op_factor, 0.75)

        c5 = createDummyContainerObject("c5", flavor="small")
        rm.allocate(c5)  # calculate allocation
        self.assertAlmostEqual(float(
            c5.resources['cpu_quota']) / c5.resources['cpu_period'], E_CPU / MAX_CU * (float(3) / 5), places=5)
        self.assertAlmostEqual(
            float(c5.resources['mem_limit'] / 1024 / 1024), float(E_MEM) / MAX_MU * 128)
        self.assertAlmostEqual(rm.cpu_op_factor, 0.6)


class testUpbDummyRM(SimpleTestTopology):
    """
    Test the UpbDummyRM resource model.
    """

    def testAllocationComputations(self):
        """
        Test the allocation procedures and correct calculations.
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 3
        E_MEM = 512
        MAX_MU = 2048
        # create dummy resource model environment
        reg = ResourceModelRegistrar(
            dc_emulation_max_cpu=E_CPU, dc_emulation_max_mem=E_MEM)
        rm = UpbDummyRM(max_cu=MAX_CU, max_mu=MAX_MU)
        reg.register("test_dc", rm)

        c1 = createDummyContainerObject("c1", flavor="small")
        rm.allocate(c1)  # calculate allocation
        self.assertEqual(len(rm._allocated_compute_instances), 1)

        c2 = createDummyContainerObject("c2", flavor="small")
        rm.allocate(c2)  # calculate allocation
        self.assertEqual(len(rm._allocated_compute_instances), 2)
