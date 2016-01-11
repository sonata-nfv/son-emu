"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""
import logging

from mininet.net import Mininet
from mininet.node import Controller, OVSKernelSwitch, Switch, Docker, Host
from mininet.cli import CLI
from mininet.log import setLogLevel, info
from mininet.link import TCLink, Link

from node import Datacenter


class DCNetwork(object):
    """
    Wraps the original Mininet class and provides
    methods to add data centers, switches, etc.

    This class is used by topology definition scripts.
    """

    def __init__(self):
        self.dcs = {}
        self.switches = {}
        self.links = []

        # create a Mininet/Dockernet network
        setLogLevel('info')  # set Mininet loglevel
        self.mnet = Mininet(controller=Controller, switch=OVSKernelSwitch)
        self.mnet.addController('c0')

    def addDatacenter(self, name):
        """
        Create and add a logical cloud data center to the network.
        """
        if name in self.dcs:
            raise Exception("Data center name already exists: %s" % name)
        dc = Datacenter(name)
        dc.net = self  # set reference to network
        self.dcs[name] = dc
        dc.create()  # finally create the data center in our Mininet instance
        logging.info("added data center: %s" % name)
        return dc

    def addSwitch(self, name):
        """
        We can also add additional SDN switches between data centers.
        """
        s = self.mnet.addSwitch(name)
        self.switches[name] = s
        logging.info("added switch: %s" % name)
        return s

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
            elif node1 in self.switches:
                node1 = self.switches[node1]
        if isinstance( node1, Datacenter ):
            node1 = node1.switch
        # ensure type of node2
        if isinstance( node2, basestring ):
            if node2 in self.dcs:
                node2 = self.dcs[node2].switch
            elif node2 in self.switches:
                node2 = self.switches[node2]
        if isinstance( node2, Datacenter ):
            node2 = node2.switch
        return self.mnet.addLink(node1, node2, **params)  # TODO we need TCLinks with user defined performance here

    def removeLink(self, link=None, node1=None, node2=None):
        """
        Removes a link. Can either be specified by link object,
        or the nodes the link connects. Wraps Dockernet method.
        """
        logging.debug("removeLink: n1=%s n2=%s" % (str(node1), str(node2)))
        return self.mnet.removeLink(link=link, node1=node1, node2=node2)

    def addDocker( self, name, **params ):
        """
        Wrapper for addDocker method provided by Dockernet.
        """
        return self.mnet.addDocker( name, **params)

    def removeDocker( self, name, **params):
        """
        Wrapper for removeHost. Just to be complete.
        """
        return self.mnet.removeDocker(name, **params)

    def start(self):
        # start
        for dc in self.dcs.itervalues():
            dc.start()
        self.mnet.start()

    def stop(self):
        self.mnet.stop()

    def CLI(self):
        CLI(self.mnet)
