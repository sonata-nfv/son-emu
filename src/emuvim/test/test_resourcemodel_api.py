import time
from emuvim.test.base import SimpleTestTopology
from emuvim.dcemulator.resourcemodel import BaseResourceModel, ResourceFlavor


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
