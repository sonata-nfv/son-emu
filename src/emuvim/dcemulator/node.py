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
from mininet.node import Docker
from mininet.link import Link
from emuvim.dcemulator.resourcemodel import NotEnoughResourcesAvailable
import logging


LOG = logging.getLogger("dcemulator.node")
LOG.setLevel(logging.DEBUG)


DCDPID_BASE = 1000  # start of switch dpid's used for data center switches
EXTSAPDPID_BASE = 2000  # start of switch dpid's used for external SAP switches


class EmulatorCompute(Docker):
    """
    Emulator specific compute node class.
    Inherits from Containernet's Docker host class.
    Represents a single container connected to a (logical)
    data center.
    We can add emulator specific helper functions to it.
    """

    def __init__(
            self, name, dimage, **kwargs):
        self.datacenter = kwargs.get("datacenter")  # pointer to current DC
        self.flavor_name = kwargs.get("flavor_name")
        self._network_state_cache = None
        LOG.debug("Starting compute instance %r in data center %r" %
                  (name, str(self.datacenter)))
        # call original Docker.__init__
        Docker.__init__(self, name, dimage, **kwargs)

    def getNetworkStatus(self):
        """
        Helper method to receive information about the virtual networks
        this compute instance is connected to.
        """
        # get all links and find dc switch interface
        networkStatusList = []
        for i in self.intfList():
            vnf_name = self.name
            vnf_interface = str(i)
            dc_port_name = self.datacenter.net.find_connected_dc_interface(
                vnf_name, vnf_interface)
            # format list of tuples (name, Ip, MAC, isUp, status, dc_portname)
            intf_dict = {'intf_name': str(i), 'ip': "{0}/{1}".format(i.IP(), i.prefixLen), 'netmask': i.prefixLen,
                         'mac': i.MAC(), 'up': i.isUp(), 'status': i.status(), 'dc_portname': dc_port_name}
            networkStatusList.append(intf_dict)
        return networkStatusList

    def getStatus(self):
        """
        Helper method to receive information about this compute instance.
        """
        # inspect container
        cinspect = self.dcli.inspect_container(self.dc)
        # inspect networking (slow, so do only once)
        if self._network_state_cache is None:
            self._network_state_cache = self.getNetworkStatus()
        # build status
        status = {}
        status["name"] = self.name
        status["network"] = self._network_state_cache
        status["docker_network"] = self.dcinfo['NetworkSettings']['IPAddress']
        status["image"] = self.dimage
        status["flavor_name"] = self.flavor_name
        status["cpu_quota"] = self.resources.get('cpu_quota')
        status["cpu_period"] = self.resources.get('cpu_period')
        status["cpu_shares"] = self.resources.get('cpu_shares')
        status["cpuset"] = self.resources.get('cpuset_cpus')
        status["mem_limit"] = self.resources.get('mem_limit')
        status["memswap_limit"] = self.resources.get('memswap_limit')
        status["state"] = cinspect["State"]
        status["id"] = cinspect["Id"]
        status["short_id"] = cinspect["Id"][:12]
        status["hostname"] = cinspect["Config"]['Hostname']
        status["datacenter"] = (None if self.datacenter is None
                                else self.datacenter.label)

        return status


class EmulatorExtSAP(object):
    """
    Emulator specific class that defines an external service access point (SAP) for the service.
    Inherits from Containernet's OVSBridge class.
    Represents a single OVS switch connected to a (logical)
    data center.
    We can add emulator specific helper functions to it.
    """

    def __init__(self, sap_name, sap_net, datacenter, **kwargs):

        self.datacenter = datacenter  # pointer to current DC
        self.net = self.datacenter.net
        self.name = sap_name

        LOG.debug("Starting ext SAP instance %r in data center %r" %
                  (sap_name, str(self.datacenter)))

        # create SAP as separate OVS switch with an assigned ip address
        self.ip = str(sap_net[1]) + '/' + str(sap_net.prefixlen)
        self.subnet = sap_net
        # allow connection to the external internet through the host
        params = dict(NAT=True)
        self.switch = self.net.addExtSAP(sap_name, self.ip, dpid=hex(
            self._get_next_extSAP_dpid())[2:], **params)
        self.switch.start()

    def _get_next_extSAP_dpid(self):
        global EXTSAPDPID_BASE
        EXTSAPDPID_BASE += 1
        return EXTSAPDPID_BASE

    def getNetworkStatus(self):
        """
        Helper method to receive information about the virtual networks
        this compute instance is connected to.
        """
        # get all links and find dc switch interface
        networkStatusList = []
        for i in self.switch.intfList():
            vnf_name = self.name
            vnf_interface = str(i)
            if vnf_interface == 'lo':
                continue
            dc_port_name = self.datacenter.net.find_connected_dc_interface(
                vnf_name, vnf_interface)
            # format list of tuples (name, Ip, MAC, isUp, status, dc_portname)
            intf_dict = {'intf_name': str(i), 'ip': self.ip, 'netmask': i.prefixLen, 'mac': i.MAC(
            ), 'up': i.isUp(), 'status': i.status(), 'dc_portname': dc_port_name}
            networkStatusList.append(intf_dict)

        return networkStatusList

    def getStatus(self):
        return {
            "name": self.switch.name,
            "datacenter": self.datacenter.name,
            "network": self.getNetworkStatus()
        }


class Datacenter(object):
    """
    Represents a logical data center to which compute resources
    (Docker containers) can be added at runtime.

    Will also implement resource bookkeeping in later versions.
    """

    DC_COUNTER = 1

    def __init__(self, label, metadata={}, resource_log_path=None):
        self.net = None  # DCNetwork to which we belong
        # each node (DC) has a short internal name used by Mininet
        # this is caused by Mininets naming limitations for swtiches etc.
        self.name = "dc%d" % Datacenter.DC_COUNTER
        Datacenter.DC_COUNTER += 1
        # use this for user defined names that can be longer than self.name
        self.label = label
        # dict to store arbitrary metadata (e.g. latitude and longitude)
        self.metadata = metadata
        # path to which resource information should be logged (e.g. for
        # experiments). None = no logging
        self.resource_log_path = resource_log_path
        # first prototype assumes one "bigswitch" per DC
        self.switch = None
        # keep track of running containers
        self.containers = {}
        # keep track of attached external access points
        self.extSAPs = {}
        # pointer to assigned resource model
        self._resource_model = None

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
        LOG.debug("created data center switch: %s" % str(self.switch))

    def start(self):
        pass

    def startCompute(self, name, image=None, command=None, network=None,
                     flavor_name="tiny", properties=dict(), **params):
        """
        Create a new container as compute resource and connect it to this
        data center.
        :param name: name (string)
        :param image: image name (string)
        :param command: command (string)
        :param network: networks list({"ip": "10.0.0.254/8"}, {"ip": "11.0.0.254/24"})
        :param flavor_name: name of the flavor for this compute container
        :param properties: dictionary of properties (key-value) that will be passed as environment variables
        :return:
        """
        assert name is not None
        default_net = {"id": "emu0"}
        # no duplications
        if name in [c.name for c in self.net.getAllContainers()]:
            raise Exception("Container with name %s already exists." % name)
        # set default parameter
        if image is None:
            image = "ubuntu:trusty"
        if network is None:
            network = {}
        if isinstance(network, dict):
            if len(network) < 1:
                # create at least one default interface
                network = default_net
            # if we have only one network, put it in a list
            network = [network]
        if isinstance(network, list):
            if len(network) < 1:
                # create at least one default interface
                network.append(default_net)

        # apply hard-set resource limits=0
        cpu_percentage = params.get('cpu_percent')
        if cpu_percentage:
            params['cpu_period'] = self.net.cpu_period
            params['cpu_quota'] = self.net.cpu_period * float(cpu_percentage)

        env = properties
        properties['VNF_NAME'] = name
        # create the container
        d = self.net.addDocker(
            str(name),
            dimage=image,
            dcmd=command,
            datacenter=self,
            flavor_name=flavor_name,
            environment=env,
            **params
        )

        # apply resource limits to container if a resource model is defined
        if self._resource_model is not None:
            try:
                self._resource_model.allocate(d)
                self._resource_model.write_allocation_log(
                    d, self.resource_log_path)
            except NotEnoughResourcesAvailable as ex:
                LOG.warning(
                    "Allocation of container %r was blocked by resource model." % name)
                LOG.info(ex.message)
                # ensure that we remove the container
                self.net.removeDocker(name)
                return None

        # connect all given networks
        # if no --net option is given, network = [{}], so 1 empty dict in the list
        # this results in 1 default interface with a default ip address
        for nw in network:
            # clean up network configuration (e.g. RTNETLINK does not allow ':'
            # in intf names
            if nw.get("id") is not None:
                nw["id"] = self._clean_ifname(nw["id"])
            # TODO we cannot use TCLink here (see:
            # https://github.com/mpeuster/containernet/issues/3)
            self.net.addLink(d, self.switch, params1=nw,
                             cls=Link, intfName1=nw.get('id'))
        # do bookkeeping
        self.containers[name] = d
        return d  # we might use UUIDs for naming later on

    def stopCompute(self, name):
        """
        Stop and remove a container from this data center.
        """
        assert name is not None
        if name not in self.containers:
            raise Exception("Container with name %s not found." % name)
        LOG.debug("Stopping compute instance %r in data center %r" %
                  (name, str(self)))

        #  stop the monitored metrics
        if self.net.monitor_agent is not None:
            self.net.monitor_agent.stop_metric(name)

        # call resource model and free resources
        if self._resource_model is not None:
            self._resource_model.free(self.containers[name])
            self._resource_model.write_free_log(
                self.containers[name], self.resource_log_path)

        # remove links
        self.net.removeLink(
            link=None, node1=self.containers[name], node2=self.switch)

        # remove container
        self.net.removeDocker("%s" % (name))
        del self.containers[name]

        return True

    def attachExternalSAP(self, sap_name, sap_net, **params):
        extSAP = EmulatorExtSAP(sap_name, sap_net, self, **params)
        # link SAP to the DC switch
        self.net.addLink(extSAP.switch, self.switch, cls=Link)
        self.extSAPs[sap_name] = extSAP

    def removeExternalSAP(self, sap_name):
        sap_switch = self.extSAPs[sap_name].switch
        # sap_switch = self.net.getNodeByName(sap_name)
        # remove link of SAP to the DC switch
        self.net.removeLink(link=None, node1=sap_switch, node2=self.switch)
        self.net.removeExtSAP(sap_name)
        del self.extSAPs[sap_name]

    def listCompute(self):
        """
        Return a list of all running containers assigned to this
        data center.
        """
        return list(self.containers.values())

    def listExtSAPs(self):
        """
        Return a list of all external SAPs assigned to this
        data center.
        """
        return list(self.extSAPs.values())

    def getStatus(self):
        """
        Return a dict with status information about this DC.
        """
        container_list = [name for name in self.containers]
        ext_saplist = [sap_name for sap_name in self.extSAPs]
        return {
            "label": self.label,
            "internalname": self.name,
            "switch": self.switch.name,
            "n_running_containers": len(self.containers),
            "metadata": self.metadata,
            "vnf_list": container_list,
            "ext SAP list": ext_saplist
        }

    def assignResourceModel(self, rm):
        """
        Assign a resource model to this DC.
        :param rm: a BaseResourceModel object
        :return:
        """
        if self._resource_model is not None:
            raise Exception(
                "There is already an resource model assigned to this DC.")
        self._resource_model = rm
        self.net.rm_registrar.register(self, rm)
        LOG.info("Assigned RM: %r to DC: %r" % (rm, self))

    @staticmethod
    def _clean_ifname(name):
        """
        Cleans up given string to be a
        RTNETLINK compatible interface name.
        :param name: string
        :return: string
        """
        if name is None:
            return "if0"
        name = name.replace(":", "-")
        name = name.replace(" ", "-")
        name = name.replace(".", "-")
        name = name.replace("_", "-")
        return name
