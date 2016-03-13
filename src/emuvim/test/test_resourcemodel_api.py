from emuvim.test.base import SimpleTestTopology
from emuvim.dcemulator.resourcemodel import BaseResourceModel


class testResourceModel(SimpleTestTopology):

    def testBaseResourceModelApi(self):
        pass
        # TODO test add flavor etc.
        # TODO test aaloc / free

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
        assert(self.net.rm_registrar.num_models == 1)
        # TODO test if alloc was called on start
        # TODO if free was called on stop
        # check connectivity by using ping
        assert(self.net.ping([self.h[0], self.h[1]]) <= 0.0)
        # stop Mininet network
        self.stopNet()
