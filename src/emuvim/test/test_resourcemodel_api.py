import time
from emuvim.test.base import SimpleTestTopology
from emuvim.dcemulator.resourcemodel import BaseResourceModel, ResourceFlavor
from emuvim.dcemulator.resourcemodel.upb.simple import UpbSimpleCloudDcRM
from emuvim.dcemulator.resourcemodel import ResourceModelRegistrar


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
        # test if allocate and free runs through
        self.assertTrue(len(r.allocate("testc", "tiny")) == 3)  # expected: 3tuple
        self.assertTrue(r.free("testc"))

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
        self.assertTrue(len(self.getDockernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check resource model and resource model registrar
        self.assertTrue(self.dc[0]._resource_model is not None)
        self.assertTrue(len(self.net.rm_registrar.resource_models) == 1)

        # check if alloc was called during startCompute
        self.assertTrue(len(r.allocated_compute_instances) == 0)
        self.dc[0].startCompute("tc1")
        time.sleep(1)
        self.assertTrue(len(r.allocated_compute_instances) == 1)
        # check if free was called during stopCompute
        self.dc[0].stopCompute("tc1")
        self.assertTrue(len(r.allocated_compute_instances) == 0)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


class testUpbSimpleCloudDcRM(SimpleTestTopology):
    """
    Test the UpbSimpleCloudDc resource model.
    """

    def testAllocation(self):
        """
        Test the allocation procedures and correct calculations.
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 100
        # create dummy resource model environment
        reg = ResourceModelRegistrar(dc_emulation_max_cpu=1.0)
        rm = UpbSimpleCloudDcRM(max_cu=100, max_mu=100)
        reg.register("test_dc", rm)

        res = rm.allocate("c1", "tiny")  # calculate allocation
        self.assertTrue(res[0] == E_CPU / MAX_CU * 1)   # validate compute result
        self.assertTrue(res[1] < 0)   # validate memory result
        self.assertTrue(res[2] < 0)   # validate disk result

        res = rm.allocate("c2", "small")  # calculate allocation
        self.assertTrue(res[0] == E_CPU / MAX_CU * 4)   # validate compute result
        self.assertTrue(res[1] < 0)   # validate memory result
        self.assertTrue(res[2] < 0)   # validate disk result

        res = rm.allocate("c3", "medium")  # calculate allocation
        self.assertTrue(res[0] == E_CPU / MAX_CU * 8)   # validate compute result
        self.assertTrue(res[1] < 0)   # validate memory result
        self.assertTrue(res[2] < 0)   # validate disk result

        res = rm.allocate("c4", "large")  # calculate allocation
        self.assertTrue(res[0] == E_CPU / MAX_CU * 16)   # validate compute result
        self.assertTrue(res[1] < 0)   # validate memory result
        self.assertTrue(res[2] < 0)   # validate disk result

        res = rm.allocate("c5", "xlarge")  # calculate allocation
        self.assertTrue(res[0] == E_CPU / MAX_CU * 32)   # validate compute result
        self.assertTrue(res[1] < 0)   # validate memory result
        self.assertTrue(res[2] < 0)   # validate disk result

        # test over provisioning exeption
        exception = False
        try:
            rm.allocate("c6", "xlarge")  # calculate allocation
            rm.allocate("c7", "xlarge")  # calculate allocation
            rm.allocate("c8", "xlarge")  # calculate allocation
            rm.allocate("c9", "xlarge")  # calculate allocation
        except Exception as e:
            self.assertTrue("Not enough compute" in e.message)
            exception = True
        self.assertTrue(exception)

    def testFree(self):
        """
        Test the free procedure.
        :return:
        """
        # config
        E_CPU = 1.0
        MAX_CU = 100
        # create dummy resource model environment
        reg = ResourceModelRegistrar(dc_emulation_max_cpu=1.0)
        rm = UpbSimpleCloudDcRM(max_cu=100, max_mu=100)
        reg.register("test_dc", rm)
        rm.allocate("c1", "tiny")  # calculate allocation
        self.assertTrue(rm.dc_alloc_cu == 1)
        rm.free("c1")
        self.assertTrue(rm.dc_alloc_cu == 0)

    def testInRealTopo(self):
        """
        Start a real container and check if limitations are really passed down to Dockernet.
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
        self.assertTrue(len(self.getDockernetContainers()) == 0)
        self.assertTrue(len(self.net.hosts) == 2)
        self.assertTrue(len(self.net.switches) == 1)
        # check resource model and resource model registrar
        self.assertTrue(self.dc[0]._resource_model is not None)
        self.assertTrue(len(self.net.rm_registrar.resource_models) == 1)

        # check if alloc was called during startCompute
        self.assertTrue(len(r.allocated_compute_instances) == 0)
        tc1 = self.dc[0].startCompute("tc1", flavor_name="tiny")
        time.sleep(1)
        self.assertTrue(len(r.allocated_compute_instances) == 1)

        # check if there is a real limitation set for containers cgroup
        self.assertEqual(tc1.cpu_period/tc1.cpu_quota, 100)

        # check if free was called during stopCompute
        self.dc[0].stopCompute("tc1")
        self.assertTrue(len(r.allocated_compute_instances) == 0)
        # check connectivity by using ping
        self.assertTrue(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()



