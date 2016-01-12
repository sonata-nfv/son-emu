"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""
import logging


DCDPID_BASE = 1000  # start of switch dpid's used for data center switches


class Datacenter(object):
    """
    Represents a logical data center to which compute resources
    (Docker containers) can be added at runtime.

    Will also implement resource bookkeeping in later versions.
    """

    def __init__(self, name):
        self.net = None  # DCNetwork to which we belong
        self.name = name
        self.switch = None  # first prototype assumes one "bigswitch" per DC
        self.containers = {}  # keep track of running containers

    def _get_next_dc_dpid(self):
        global DCDPID_BASE
        DCDPID_BASE += 1
        return DCDPID_BASE

    def create(self):
        """
        Each data center is represented by a single switch to which
        compute resources can be connected at run time.

        TODO: This will be changed in the future to support multiple networks
        per data center
        """
        self.switch = self.net.mnet.addSwitch(
            "%s.s1" % self.name, dpid=hex(self._get_next_dc_dpid())[2:])
        logging.debug("created data center switch: %s" % str(self.switch))

    def start(self):
        pass

    def addCompute(self, name):
        """
        Create a new container as compute resource and connect it to this
        data center.
        """
        # TODO ip management
        d = self.net.addDocker("%s" % (name), dimage="ubuntu")
        self.net.addLink(d, self.switch) #params1={"ip": "10.0.0.254/8"}
        self.containers[name] = d

    def removeCompute(self, name):
        """
        Stop and remove a container from this data center.
        """
        assert name in self.containers
        self.net.removeLink(
            link=None, node1=self.containers[name], node2=self.switch)
        self.net.removeDocker("%s" % (name))
        del self.containers[name]
