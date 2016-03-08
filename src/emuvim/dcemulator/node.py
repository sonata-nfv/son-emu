"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""
from mininet.node import Docker
from mininet.link import Link
import logging


DCDPID_BASE = 1000  # start of switch dpid's used for data center switches


class EmulatorCompute(Docker):
    """
    Emulator specific compute node class.
    Inherits from Dockernet's Docker host class.
    Represents a single container connected to a (logical)
    data center.
    We can add emulator specific helper functions to it.
    """

    def __init__(
            self, name, dimage, **kwargs):
        logging.debug("Create EmulatorCompute instance: %s" % name)
        self.datacenter = None  # pointer to current DC

        # call original Docker.__init__
        Docker.__init__(self, name, dimage, **kwargs)

    def getNetworkStatus(self):
        """
        Helper method to receive information about the virtual networks
        this compute instance is connected to.
        """
        # format list of tuples (name, Ip, MAC, isUp, status)
        return [(str(i), i.IP(), i.MAC(), i.isUp(), i.status())
                for i in self.intfList()]

    def getStatus(self):
        """
        Helper method to receive information about this compute instance.
        """
        status = {}
        status["name"] = self.name
        status["network"] = self.getNetworkStatus()
        status["image"] = self.dimage
        status["cpu_quota"] = self.cpu_quota
        status["cpu_period"] = self.cpu_period
        status["cpu_shares"] = self.cpu_shares
        status["cpuset"] = self.cpuset
        status["mem_limit"] = self.mem_limit
        status["memswap_limit"] = self.memswap_limit
        status["state"] = self.dcli.inspect_container(self.dc)["State"]
        status["id"] = self.dcli.inspect_container(self.dc)["Id"]
        status["datacenter"] = (None if self.datacenter is None
                                else self.datacenter.label)
        return status


class Datacenter(object):
    """
    Represents a logical data center to which compute resources
    (Docker containers) can be added at runtime.

    Will also implement resource bookkeeping in later versions.
    """

    DC_COUNTER = 1

    def __init__(self, label, metadata={}):
        self.net = None  # DCNetwork to which we belong
        # each node (DC) has a short internal name used by Mininet
        # this is caused by Mininets naming limitations for swtiches etc.
        self.name = "dc%d" % Datacenter.DC_COUNTER
        Datacenter.DC_COUNTER += 1
        # use this for user defined names that can be longer than self.name
        self.label = label  
        # dict to store arbitrary metadata (e.g. latitude and longitude)
        self.metadata = metadata
        self.switch = None  # first prototype assumes one "bigswitch" per DC
        self.containers = {}  # keep track of running containers

    def __repr__(self):
        return self.label

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
        self.switch = self.net.addSwitch(
            "%s.s1" % self.name, dpid=hex(self._get_next_dc_dpid())[2:])
        logging.debug("created data center switch: %s" % str(self.switch))

    def start(self):
        pass

    def startCompute(self, name, image=None, command=None, network=None):
        """
        Create a new container as compute resource and connect it to this
        data center.
        :param name: name (string)
        :param image: image name (string)
        :param command: command (string)
        :param network: networks list({"ip": "10.0.0.254/8"}, {"ip": "11.0.0.254/24"})
        :return:
        """
        assert name is not None
        # no duplications
        if name in [c.name for c in self.net.getAllContainers()]:
            raise Exception("Container with name %s already exists." % name)
        # set default parameter
        if image is None:
            image = "ubuntu"
        if network is None:
            network = {}  # {"ip": "10.0.0.254/8"}
        if isinstance(network, dict):
            network = [network]  # if we have only one network, put it in a list
        if isinstance(network, list):
            if len(network) < 1:
                network.append({})

        # create the container
        d = self.net.addDocker("%s" % (name), dimage=image, dcmd=command)
        # connect all given networks
        for nw in network:
            # TODO we cannot use TCLink here (see: https://github.com/mpeuster/dockernet/issues/3)
            self.net.addLink(d, self.switch, params1=nw, cls=Link)
        # do bookkeeping
        self.containers[name] = d
        d.datacenter = self
        return d  # we might use UUIDs for naming later on

    def stopCompute(self, name):
        """
        Stop and remove a container from this data center.
        """
        assert name is not None
        if name not in self.containers:
            raise Exception("Container with name %s not found." % name)
        self.net.removeLink(
            link=None, node1=self.containers[name], node2=self.switch)
        self.net.removeDocker("%s" % (name))
        del self.containers[name]
        return True

    def listCompute(self):
        """
        Return a list of all running containers assigned to this
        data center.
        """
        return list(self.containers.itervalues())

    def getStatus(self):
        """
        Return a dict with status information about this DC.
        """
        return {
            "label": self.label,
            "internalname": self.name,
            "switch": self.switch.name,
            "n_running_containers": len(self.containers),
            "metadata": self.metadata
        }
