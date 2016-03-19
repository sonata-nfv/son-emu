import time
from emuvim.test.base import SimpleTestTopology
from emuvim.dcemulator.resourcemodel import BaseResourceModel, ResourceFlavor
from emuvim.dcemulator.resourcemodel.upb.simple import UpbSimpleCloudDcRM
from emuvim.dcemulator.resourcemodel import ResourceModelRegistrar


class testResourceModel(SimpleTestTopology):

    def testBaseResourceModelApi(self):
        r = BaseResourceModel()
        # check if default flavors are there
        assert(len(r._flavors) == 5)
        # check addFlavor functionality
        f = ResourceFlavor("test", {"testmetric": 42})
        r.addFlavour(f)
        assert("test" in r._flavors)
        assert(r._flavors.get("test").get("testmetric") == 42)
        # test if allocate and free runs through
        assert(len(r.allocate("testc", "tiny")) == 3)  # expected: 3tuple
        assert(r.free("testc"))

    def testAddRmToDc(self):
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
        assert(len(self.getDockernetContainers()) == 0)
        assert(len(self.net.hosts) == 2)
        assert(len(self.net.switches) == 1)
        # check resource model and resource model registrar
        assert(self.dc[0]._resource_model is not None)
        assert(len(self.net.rm_registrar.resource_models) == 1)

        # check if alloc was called during startCompute
        assert(len(r.allocated_compute_instances) == 0)
        self.dc[0].startCompute("tc1")
        time.sleep(1)
        assert(len(r.allocated_compute_instances) == 1)
        # check if free was called during stopCompute
        self.dc[0].stopCompute("tc1")
        assert(len(r.allocated_compute_instances) == 0)
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()


class testUpbSimpleCloudDcRM(SimpleTestTopology):
    """
    Test the UpbSimpleCloudDc resource model.
    """
    def testAllocation(self):
        # config
        E_CPU = 1.0
        MAX_CU = 100
        # create dummy resource model environment
        reg = ResourceModelRegistrar(dc_emulation_max_cpu=1.0)
        rm = UpbSimpleCloudDcRM(max_cu=100, max_mu=100)
        reg.register("test_dc", rm)

        res = rm.allocate("c1", "tiny")  # calculate allocation
        assert(res[0] == E_CPU / MAX_CU * 1)   # validate compute result
        assert(res[1] < 0)   # validate memory result
        assert(res[2] < 0)   # validate disk result

        res = rm.allocate("c2", "small")  # calculate allocation
        assert(res[0] == E_CPU / MAX_CU * 4)   # validate compute result
        assert(res[1] < 0)   # validate memory result
        assert(res[2] < 0)   # validate disk result

        res = rm.allocate("c3", "medium")  # calculate allocation
        assert(res[0] == E_CPU / MAX_CU * 8)   # validate compute result
        assert(res[1] < 0)   # validate memory result
        assert(res[2] < 0)   # validate disk result

        res = rm.allocate("c4", "large")  # calculate allocation
        assert(res[0] == E_CPU / MAX_CU * 16)   # validate compute result
        assert(res[1] < 0)   # validate memory result
        assert(res[2] < 0)   # validate disk result

        res = rm.allocate("c5", "xlarge")  # calculate allocation
        assert(res[0] == E_CPU / MAX_CU * 32)   # validate compute result
        assert(res[1] < 0)   # validate memory result
        assert(res[2] < 0)   # validate disk result

        # test over provisioning exeption
        exception = False
        try:
            rm.allocate("c6", "xlarge")  # calculate allocation
            rm.allocate("c7", "xlarge")  # calculate allocation
            rm.allocate("c8", "xlarge")  # calculate allocation
            rm.allocate("c9", "xlarge")  # calculate allocation
        except Exception as e:
            assert("Not enough compute" in e.message)
            exception = True
        assert(exception)

    def testFree(self):
        # config
        E_CPU = 1.0
        MAX_CU = 100
        # create dummy resource model environment
        reg = ResourceModelRegistrar(dc_emulation_max_cpu=1.0)
        rm = UpbSimpleCloudDcRM(max_cu=100, max_mu=100)
        reg.register("test_dc", rm)
        rm.allocate("c1", "tiny")  # calculate allocation
        assert(rm.dc_alloc_cu == 1)
        rm.free("c1")
        assert(rm.dc_alloc_cu == 0)



