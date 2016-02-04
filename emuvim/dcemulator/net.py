"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""
import logging

from mininet.net import Dockernet
from mininet.node import Controller, OVSKernelSwitch, Switch, Docker, Host
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Link

from node import Datacenter, EmulatorCompute


class DCNetwork(Dockernet):
    """
    Wraps the original Mininet/Dockernet class and provides
    methods to add data centers, switches, etc.

    This class is used by topology definition scripts.
    """

    def __init__(self, **kwargs):
        self.dcs = {}
        # create a Mininet/Dockernet network
        # call original Docker.__init__ and setup default controller
        Dockernet.__init__(
            self, controller=Controller, switch=OVSKernelSwitch, **kwargs)
        self.addController('c0')

    def addDatacenter(self, label):
        """
        Create and add a logical cloud data center to the network.
        """
        if label in self.dcs:
            raise Exception("Data center label already exists: %s" % label)
        dc = Datacenter(label)
        dc.net = self  # set reference to network
        self.dcs[label] = dc
        dc.create()  # finally create the data center in our Mininet instance
        logging.info("added data center: %s" % label)
        return dc

    def addLink(self, node1, node2, **params):
        """
        Able to handle Datacenter objects as link
        end points.
        """
        assert node1 is not None
        assert node2 is not None
        logging.debug("addLink: n1=%s n2=%s" % (str(node1), str(node2)))
        # ensure type of node1
        if isinstance( node1, basestring ):
            if node1 in self.dcs:
                node1 = self.dcs[node1].switch
        if isinstance( node1, Datacenter ):
            node1 = node1.switch
        # ensure type of node2
        if isinstance( node2, basestring ):
            if node2 in self.dcs:
                node2 = self.dcs[node2].switch
        if isinstance( node2, Datacenter ):
            node2 = node2.switch
        # try to give containers a default IP
        if isinstance( node1, Docker ):
            if not "params1" in params:
                params["params1"] = {}
            if not "ip" in params["params1"]:
                params["params1"]["ip"] = self.getNextIp()
        if isinstance( node2, Docker ):
            if not "params2" in params:
                params["params2"] = {}
            if not "ip" in params["params2"]:
                params["params2"]["ip"] = self.getNextIp()

        return Dockernet.addLink(self, node1, node2, **params)  # TODO we need TCLinks with user defined performance here

    def addDocker( self, label, **params ):
        """
        Wrapper for addDocker method to use custom container class.
        """
        return Dockernet.addDocker(self, label, cls=EmulatorCompute, **params)

    def getAllContainers(self):
        """
        Returns a list with all containers within all data centers.
        """
        all_containers = []
        for dc in self.dcs.itervalues():
            all_containers += dc.listCompute()
        return all_containers

    def start(self):
        # start
        for dc in self.dcs.itervalues():
            dc.start()
        Dockernet.start(self)

    def stop(self):
        Dockernet.stop(self)

    def CLI(self):
        CLI(self)
