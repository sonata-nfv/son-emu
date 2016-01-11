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
        #TODO connect container to DC's swtich
        d1 = self.net.addDocker("%s.%s" % (self.name, name), dimage="ubuntu")
        l1 = self.net.addLink(d1, self.switch)

    def removeCompute(self, name):
        #TODO disconnect container to DC's swtich
        self.net.removeDocker("%s.%s" % (self.name, name))
