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
import logging

import site
import time
from subprocess import Popen
import re
import requests
import os
import json

from mininet.net import Containernet
from mininet.node import OVSSwitch, OVSKernelSwitch, Docker, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.clean import cleanup
import networkx as nx
from emuvim.dcemulator.monitoring import DCNetworkMonitor
from emuvim.dcemulator.node import Datacenter, EmulatorCompute
from emuvim.dcemulator.resourcemodel import ResourceModelRegistrar

LOG = logging.getLogger("dcemulator.net")
LOG.setLevel(logging.DEBUG)

# default CPU period used for cpu percentage-based cfs values (microseconds)
CPU_PERIOD = 1000000

# default priority setting for added flow-rules
DEFAULT_PRIORITY = 1000
# default cookie number for new flow-rules
DEFAULT_COOKIE = 10


class DCNetwork(Containernet):
    """
    Wraps the original Mininet/Containernet class and provides
    methods to add data centers, switches, etc.

    This class is used by topology definition scripts.
    """

    def __init__(self, controller=RemoteController, monitor=False,
                 enable_learning=False,
                 # learning switch behavior of the default ovs switches icw Ryu
                 # controller can be turned off/on, needed for E-LAN
                 # functionality
                 dc_emulation_max_cpu=1.0,  # fraction of overall CPU time for emulation
                 dc_emulation_max_mem=512,  # emulation max mem in MB
                 **kwargs):
        """
        Create an extended version of a Containernet network
        :param dc_emulation_max_cpu: max. CPU time used by containers in data centers
        :param kwargs: path through for Mininet parameters
        :return:
        """
        # members
        self.dcs = {}
        self.ryu_process = None
        # list of deployed nsds.E_Lines and E_LANs (uploaded from the dummy
        # gatekeeper)
        self.deployed_nsds = []
        self.deployed_elines = []
        self.deployed_elans = []
        self.installed_chains = []

        # always cleanup environment before we start the emulator
        self.killRyu()
        cleanup()

        # call original Docker.__init__ and setup default controller
        Containernet.__init__(
            self, switch=OVSKernelSwitch, controller=controller, **kwargs)

        # default switch configuration
        enable_ryu_learning = False
        if enable_learning:
            self.failMode = 'standalone'
            enable_ryu_learning = True
        else:
            self.failMode = 'secure'

        # Ryu management
        if controller == RemoteController:
            # start Ryu controller
            self.startRyu(learning_switch=enable_ryu_learning)

        # add the specified controller
        self.addController('c0', controller=controller)

        # graph of the complete DC network
        self.DCNetwork_graph = nx.MultiDiGraph()

        # initialize pool of vlan tags to setup the SDN paths
        self.vlans = range(1, 4095)[::-1]

        # link to Ryu REST_API
        ryu_ip = 'localhost'
        ryu_port = '8080'
        self.ryu_REST_api = 'http://{0}:{1}'.format(ryu_ip, ryu_port)
        self.RyuSession = requests.Session()

        # monitoring agent
        if monitor:
            self.monitor_agent = DCNetworkMonitor(self)
        else:
            self.monitor_agent = None

        # initialize resource model registrar
        self.rm_registrar = ResourceModelRegistrar(
            dc_emulation_max_cpu, dc_emulation_max_mem)
        self.cpu_period = CPU_PERIOD

    def addDatacenter(self, label, metadata={}, resource_log_path=None):
        """
        Create and add a logical cloud data center to the network.
        """
        if label in self.dcs:
            raise Exception("Data center label already exists: %s" % label)
        dc = Datacenter(label, metadata=metadata,
                        resource_log_path=resource_log_path)
        dc.net = self  # set reference to network
        self.dcs[label] = dc
        dc.create()  # finally create the data center in our Mininet instance
        LOG.info("added data center: %s" % label)
        return dc

    def addLink(self, node1, node2, **params):
        """
        Able to handle Datacenter objects as link
        end points.
        """
        assert node1 is not None
        assert node2 is not None

        # ensure type of node1
        if isinstance(node1, basestring):
            if node1 in self.dcs:
                node1 = self.dcs[node1].switch
        if isinstance(node1, Datacenter):
            node1 = node1.switch
        # ensure type of node2
        if isinstance(node2, basestring):
            if node2 in self.dcs:
                node2 = self.dcs[node2].switch
        if isinstance(node2, Datacenter):
            node2 = node2.switch
        # try to give containers a default IP
        if isinstance(node1, Docker):
            if "params1" not in params:
                params["params1"] = {}
            if "ip" not in params["params1"]:
                params["params1"]["ip"] = self.getNextIp()
        if isinstance(node2, Docker):
            if "params2" not in params:
                params["params2"] = {}
            if "ip" not in params["params2"]:
                params["params2"]["ip"] = self.getNextIp()
        # ensure that we allow TCLinks between data centers
        # TODO this is not optimal, we use cls=Link for containers and TCLink for data centers
        # see Containernet issue:
        # https://github.com/mpeuster/containernet/issues/3
        if "cls" not in params:
            params["cls"] = TCLink

        link = Containernet.addLink(self, node1, node2, **params)

        # try to give container interfaces a default id
        node1_port_id = node1.ports[link.intf1]
        if isinstance(node1, Docker):
            if "id" in params["params1"]:
                node1_port_id = params["params1"]["id"]
        node1_port_name = link.intf1.name

        node2_port_id = node2.ports[link.intf2]
        if isinstance(node2, Docker):
            if "id" in params["params2"]:
                node2_port_id = params["params2"]["id"]
        node2_port_name = link.intf2.name

        # add edge and assigned port number to graph in both directions between node1 and node2
        # port_id: id given in descriptor (if available, otherwise same as port)
        # port: portnumber assigned by Containernet

        attr_dict = {}
        # possible weight metrics allowed by TClink class:
        weight_metrics = ['bw', 'delay', 'jitter', 'loss']
        edge_attributes = [p for p in params if p in weight_metrics]
        for attr in edge_attributes:
            # if delay: strip ms (need number as weight in graph)
            match = re.search('([0-9]*\.?[0-9]+)', str(params[attr]))
            if match:
                attr_number = match.group(1)
            else:
                attr_number = None
            attr_dict[attr] = attr_number

        attr_dict2 = {'src_port_id': node1_port_id, 'src_port_nr': node1.ports[link.intf1],
                      'src_port_name': node1_port_name,
                      'dst_port_id': node2_port_id, 'dst_port_nr': node2.ports[link.intf2],
                      'dst_port_name': node2_port_name}
        attr_dict2.update(attr_dict)
        self.DCNetwork_graph.add_edge(
            node1.name, node2.name, attr_dict=attr_dict2)

        attr_dict2 = {'src_port_id': node2_port_id, 'src_port_nr': node2.ports[link.intf2],
                      'src_port_name': node2_port_name,
                      'dst_port_id': node1_port_id, 'dst_port_nr': node1.ports[link.intf1],
                      'dst_port_name': node1_port_name}
        attr_dict2.update(attr_dict)
        self.DCNetwork_graph.add_edge(
            node2.name, node1.name, attr_dict=attr_dict2)

        LOG.debug("addLink: n1={0} intf1={1} -- n2={2} intf2={3}".format(
            str(node1), node1_port_name, str(node2), node2_port_name))

        return link

    def removeLink(self, link=None, node1=None, node2=None):
        """
        Remove the link from the Containernet and the networkx graph
        """
        if link is not None:
            node1 = link.intf1.node
            node2 = link.intf2.node
        assert node1 is not None
        assert node2 is not None
        Containernet.removeLink(self, link=link, node1=node1, node2=node2)
        # TODO we might decrease the loglevel to debug:
        try:
            self.DCNetwork_graph.remove_edge(node2.name, node1.name)
        except BaseException:
            LOG.warning("%s, %s not found in DCNetwork_graph." %
                        ((node2.name, node1.name)))
        try:
            self.DCNetwork_graph.remove_edge(node1.name, node2.name)
        except BaseException:
            LOG.warning("%s, %s not found in DCNetwork_graph." %
                        ((node1.name, node2.name)))

    def addDocker(self, label, **params):
        """
        Wrapper for addDocker method to use custom container class.
        """
        self.DCNetwork_graph.add_node(label, type=params.get('type', 'docker'))
        return Containernet.addDocker(
            self, label, cls=EmulatorCompute, **params)

    def removeDocker(self, label, **params):
        """
        Wrapper for removeDocker method to update graph.
        """
        self.DCNetwork_graph.remove_node(label)
        return Containernet.removeDocker(self, label, **params)

    def addExtSAP(self, sap_name, sap_ip, **params):
        """
        Wrapper for addExtSAP method to store SAP  also in graph.
        """
        # make sure that 'type' is set
        params['type'] = params.get('type', 'sap_ext')
        self.DCNetwork_graph.add_node(sap_name, type=params['type'])
        return Containernet.addExtSAP(self, sap_name, sap_ip, **params)

    def removeExtSAP(self, sap_name, **params):
        """
        Wrapper for removeExtSAP method to remove SAP  also from graph.
        """
        self.DCNetwork_graph.remove_node(sap_name)
        return Containernet.removeExtSAP(self, sap_name)

    def addSwitch(self, name, add_to_graph=True, **params):
        """
        Wrapper for addSwitch method to store switch also in graph.
        """

        # add this switch to the global topology overview
        if add_to_graph:
            self.DCNetwork_graph.add_node(
                name, type=params.get('type', 'switch'))

        # set the learning switch behavior
        if 'failMode' in params:
            failMode = params['failMode']
        else:
            failMode = self.failMode

        s = Containernet.addSwitch(
            self, name, protocols='OpenFlow10,OpenFlow12,OpenFlow13', failMode=failMode, **params)

        return s

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
        Containernet.start(self)

    def stop(self):

        # stop the monitor agent
        if self.monitor_agent is not None:
            self.monitor_agent.stop()

        # stop emulator net
        Containernet.stop(self)

        # stop Ryu controller
        self.killRyu()

    def CLI(self):
        CLI(self)

    def setLAN(self, vnf_list):
        """
        setup an E-LAN network by assigning the same VLAN tag to each DC interface of the VNFs in the E-LAN

        :param vnf_list: names of the VNFs in this E-LAN  [{name:,interface:},...]
        :return:
        """
        src_sw = None
        src_sw_inport_name = None

        # get a vlan tag for this E-LAN
        vlan = self.vlans.pop()

        for vnf in vnf_list:
            vnf_src_name = vnf['name']
            vnf_src_interface = vnf['interface']

            # check if port is specified (vnf:port)
            if vnf_src_interface is None:
                # take first interface by default
                connected_sw = self.DCNetwork_graph.neighbors(vnf_src_name)[0]
                link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
                vnf_src_interface = link_dict[0]['src_port_id']

            for connected_sw in self.DCNetwork_graph.neighbors(vnf_src_name):
                link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
                for link in link_dict:
                    if (link_dict[link]['src_port_id'] == vnf_src_interface or
                            link_dict[link]['src_port_name'] == vnf_src_interface):  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                        # found the right link and connected switch
                        src_sw = connected_sw
                        src_sw_inport_name = link_dict[link]['dst_port_name']
                        break

            # set the tag on the dc switch interface
            LOG.debug('set E-LAN: vnf name: {0} interface: {1} tag: {2}'.format(
                vnf_src_name, vnf_src_interface, vlan))
            switch_node = self.getNodeByName(src_sw)
            self._set_vlan_tag(switch_node, src_sw_inport_name, vlan)

    def _addMonitorFlow(self, vnf_src_name, vnf_dst_name, vnf_src_interface=None, vnf_dst_interface=None,
                        tag=None, **kwargs):
        """
        Add a monitoring flow entry that adds a special flowentry/counter at the begin or end of a chain.
        So this monitoring flowrule exists on top of a previously defined chain rule and uses the same vlan tag/routing.
        :param vnf_src_name:
        :param vnf_dst_name:
        :param vnf_src_interface:
        :param vnf_dst_interface:
        :param tag: vlan tag to be used for this chain (same tag as existing chain)
        :param monitor_placement: 'tx' or 'rx' indicating to place the extra flowentry resp. at the beginning or end of the chain
        :return:
        """

        src_sw = None
        src_sw_inport_nr = 0
        src_sw_inport_name = None
        dst_sw = None
        dst_sw_outport_nr = 0
        dst_sw_outport_name = None

        LOG.debug("call AddMonitorFlow vnf_src_name=%r, vnf_src_interface=%r, vnf_dst_name=%r, vnf_dst_interface=%r",
                  vnf_src_name, vnf_src_interface, vnf_dst_name, vnf_dst_interface)

        # check if port is specified (vnf:port)
        if vnf_src_interface is None:
            # take first interface by default
            connected_sw = self.DCNetwork_graph.neighbors(vnf_src_name)[0]
            link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
            vnf_src_interface = link_dict[0]['src_port_id']

        for connected_sw in self.DCNetwork_graph.neighbors(vnf_src_name):
            link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
            for link in link_dict:
                if (link_dict[link]['src_port_id'] == vnf_src_interface or
                        link_dict[link]['src_port_name'] == vnf_src_interface):  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                    # found the right link and connected switch
                    src_sw = connected_sw
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']
                    src_sw_inport_name = link_dict[link]['dst_port_name']
                    break

        if vnf_dst_interface is None:
            # take first interface by default
            connected_sw = self.DCNetwork_graph.neighbors(vnf_dst_name)[0]
            link_dict = self.DCNetwork_graph[connected_sw][vnf_dst_name]
            vnf_dst_interface = link_dict[0]['dst_port_id']

        vnf_dst_name = vnf_dst_name.split(':')[0]
        for connected_sw in self.DCNetwork_graph.neighbors(vnf_dst_name):
            link_dict = self.DCNetwork_graph[connected_sw][vnf_dst_name]
            for link in link_dict:
                if link_dict[link]['dst_port_id'] == vnf_dst_interface or \
                        link_dict[link]['dst_port_name'] == vnf_dst_interface:  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                    # found the right link and connected switch
                    dst_sw = connected_sw
                    dst_sw_outport_nr = link_dict[link]['src_port_nr']
                    dst_sw_outport_name = link_dict[link]['src_port_name']
                    break

        if not tag >= 0:
            LOG.exception('tag not valid: {0}'.format(tag))

        # get shortest path
        try:
            # returns the first found shortest path
            # if all shortest paths are wanted, use: all_shortest_paths
            path = nx.shortest_path(
                self.DCNetwork_graph, src_sw, dst_sw, weight=kwargs.get('weight'))
        except BaseException:
            LOG.exception("No path could be found between {0} and {1} using src_sw={2} and dst_sw={3}".format(
                vnf_src_name, vnf_dst_name, src_sw, dst_sw))
            LOG.debug("Graph nodes: %r" % self.DCNetwork_graph.nodes())
            LOG.debug("Graph edges: %r" % self.DCNetwork_graph.edges())
            for e, v in self.DCNetwork_graph.edges():
                LOG.debug("%r" % self.DCNetwork_graph[e][v])
            return "No path could be found between {0} and {1}".format(
                vnf_src_name, vnf_dst_name)

        LOG.debug("Creating path between {0} and {1}: {2}".format(
            vnf_src_name, vnf_dst_name, path))

        current_hop = src_sw
        switch_inport_nr = src_sw_inport_nr

        cmd = kwargs.get('cmd')

        # iterate through the path to install the flow-entries
        for i in range(0, len(path)):
            current_node = self.getNodeByName(current_hop)

            if path.index(current_hop) < len(path) - 1:
                next_hop = path[path.index(current_hop) + 1]
            else:
                # last switch reached
                next_hop = vnf_dst_name

            next_node = self.getNodeByName(next_hop)

            if next_hop == vnf_dst_name:
                switch_outport_nr = dst_sw_outport_nr
                LOG.debug("end node reached: {0}".format(vnf_dst_name))
            elif not isinstance(next_node, OVSSwitch):
                LOG.info("Next node: {0} is not a switch".format(next_hop))
                return "Next node: {0} is not a switch".format(next_hop)
            else:
                # take first link between switches by default
                index_edge_out = 0
                switch_outport_nr = self.DCNetwork_graph[current_hop][next_hop][index_edge_out]['src_port_nr']

            # set of entry via ovs-ofctl
            if isinstance(current_node, OVSSwitch):
                kwargs['vlan'] = tag
                kwargs['path'] = path
                kwargs['current_hop'] = current_hop
                kwargs['switch_inport_name'] = src_sw_inport_name
                kwargs['switch_outport_name'] = dst_sw_outport_name
                kwargs['skip_vlan_tag'] = True
                kwargs['pathindex'] = i

                monitor_placement = kwargs.get('monitor_placement').strip()
                # put monitor flow at the dst switch
                insert_flow = False
                # first node:
                if monitor_placement == 'tx' and path.index(current_hop) == 0:
                    insert_flow = True
                # put monitoring flow at the src switch
                # last node:
                elif monitor_placement == 'rx' and path.index(current_hop) == len(path) - 1:
                    insert_flow = True
                elif monitor_placement not in ['rx', 'tx']:
                    LOG.exception(
                        'invalid monitor command: {0}'.format(monitor_placement))

                if self.controller == RemoteController and insert_flow:
                    # set flow entry via ryu rest api
                    self._set_flow_entry_ryu_rest(
                        current_node, switch_inport_nr, switch_outport_nr, **kwargs)
                    break
                elif insert_flow:
                    # set flow entry via ovs-ofctl
                    self._set_flow_entry_dpctl(
                        current_node, switch_inport_nr, switch_outport_nr, **kwargs)
                    break

            # take first link between switches by default
            if isinstance(next_node, OVSSwitch):
                switch_inport_nr = self.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                current_hop = next_hop

        return "path {2} between {0} and {1}".format(
            vnf_src_name, vnf_dst_name, cmd)

    def setChain(self, vnf_src_name, vnf_dst_name,
                 vnf_src_interface=None, vnf_dst_interface=None, **kwargs):
        """
        Chain 2 vnf interfaces together by installing the flowrules in the switches along their path.
        Currently the path is found using the default networkx shortest path function.
        Each chain gets a unique vlan id , so different chains wil not interfere.

        :param vnf_src_name: vnf name (string)
        :param vnf_dst_name: vnf name (string)
        :param vnf_src_interface: source interface name  (string)
        :param vnf_dst_interface: destination interface name  (string)
        :param cmd: 'add-flow' (default) to add a chain, 'del-flows' to remove a chain
        :param cookie: cookie for the installed flowrules (can be used later as identifier for a set of installed chains)
        :param match: custom match entry to be added to the flowrules (default: only in_port and vlan tag)
        :param priority: custom flowrule priority
        :param monitor: boolean to indicate whether this chain is a monitoring chain
        :param tag: vlan tag to be used for this chain (pre-defined or new one if none is specified)
        :param skip_vlan_tag: boolean to indicate if a vlan tag should be appointed to this flow or not
        :param path: custom path between the two VNFs (list of switches)
        :return: output log string
        """

        # special procedure for monitoring flows
        if kwargs.get('monitor'):

            # check if chain already exists
            found_chains = [chain_dict for chain_dict in self.installed_chains if
                            (chain_dict['vnf_src_name'] == vnf_src_name and
                             chain_dict['vnf_src_interface'] == vnf_src_interface and
                             chain_dict['vnf_dst_name'] == vnf_dst_name and
                             chain_dict['vnf_dst_interface'] == vnf_dst_interface)]

            if len(found_chains) > 0:
                # this chain exists, so need an extra monitoring flow
                # assume only 1 chain per vnf/interface pair
                LOG.debug('*** installing monitoring chain on top of pre-defined chain from {0}:{1} -> {2}:{3}'.
                          format(vnf_src_name, vnf_src_interface, vnf_dst_name, vnf_dst_interface))
                tag = found_chains[0]['tag']
                ret = self._addMonitorFlow(vnf_src_name, vnf_dst_name, vnf_src_interface, vnf_dst_interface,
                                           tag=tag, table_id=0, **kwargs)
                return ret
            else:
                # no chain existing (or E-LAN) -> install normal chain
                LOG.warning('*** installing monitoring chain without pre-defined NSD chain from {0}:{1} -> {2}:{3}'.
                            format(vnf_src_name, vnf_src_interface, vnf_dst_name, vnf_dst_interface))
                pass

        cmd = kwargs.get('cmd', 'add-flow')
        if cmd == 'add-flow' or cmd == 'del-flows':
            ret = self._chainAddFlow(
                vnf_src_name, vnf_dst_name, vnf_src_interface, vnf_dst_interface, **kwargs)
            if kwargs.get('bidirectional'):
                if kwargs.get('path') is not None:
                    kwargs['path'] = list(reversed(kwargs.get('path')))
                ret = ret + '\n' + \
                    self._chainAddFlow(
                        vnf_dst_name, vnf_src_name, vnf_dst_interface, vnf_src_interface, **kwargs)

        else:
            ret = "Command unknown"

        return ret

    def _chainAddFlow(self, vnf_src_name, vnf_dst_name,
                      vnf_src_interface=None, vnf_dst_interface=None, **kwargs):

        src_sw = None
        src_sw_inport_nr = 0
        src_sw_inport_name = None
        dst_sw = None
        dst_sw_outport_nr = 0
        dst_sw_outport_name = None

        LOG.debug("call chainAddFlow vnf_src_name=%r, vnf_src_interface=%r, vnf_dst_name=%r, vnf_dst_interface=%r",
                  vnf_src_name, vnf_src_interface, vnf_dst_name, vnf_dst_interface)

        # check if port is specified (vnf:port)
        if vnf_src_interface is None:
            # take first interface by default
            connected_sw = self.DCNetwork_graph.neighbors(vnf_src_name)[0]
            link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
            vnf_src_interface = link_dict[0]['src_port_id']

        for connected_sw in self.DCNetwork_graph.neighbors(vnf_src_name):
            link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
            for link in link_dict:
                if (link_dict[link]['src_port_id'] == vnf_src_interface or
                        link_dict[link]['src_port_name'] == vnf_src_interface):  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                    # found the right link and connected switch
                    src_sw = connected_sw
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']
                    src_sw_inport_name = link_dict[link]['dst_port_name']
                    break

        if vnf_dst_interface is None:
            # take first interface by default
            connected_sw = self.DCNetwork_graph.neighbors(vnf_dst_name)[0]
            link_dict = self.DCNetwork_graph[connected_sw][vnf_dst_name]
            vnf_dst_interface = link_dict[0]['dst_port_id']

        vnf_dst_name = vnf_dst_name.split(':')[0]
        for connected_sw in self.DCNetwork_graph.neighbors(vnf_dst_name):
            link_dict = self.DCNetwork_graph[connected_sw][vnf_dst_name]
            for link in link_dict:
                if link_dict[link]['dst_port_id'] == vnf_dst_interface or \
                        link_dict[link]['dst_port_name'] == vnf_dst_interface:  # Fix: we might also get interface names, e.g, from a son-emu-cli call
                    # found the right link and connected switch
                    dst_sw = connected_sw
                    dst_sw_outport_nr = link_dict[link]['src_port_nr']
                    dst_sw_outport_name = link_dict[link]['src_port_name']
                    break

        path = kwargs.get('path')
        if path is None:
            # get shortest path
            try:
                # returns the first found shortest path
                # if all shortest paths are wanted, use: all_shortest_paths
                path = nx.shortest_path(
                    self.DCNetwork_graph, src_sw, dst_sw, weight=kwargs.get('weight'))
            except BaseException:
                LOG.exception("No path could be found between {0} and {1} using src_sw={2} and dst_sw={3}".format(
                    vnf_src_name, vnf_dst_name, src_sw, dst_sw))
                LOG.debug("Graph nodes: %r" % self.DCNetwork_graph.nodes())
                LOG.debug("Graph edges: %r" % self.DCNetwork_graph.edges())
                for e, v in self.DCNetwork_graph.edges():
                    LOG.debug("%r" % self.DCNetwork_graph[e][v])
                return "No path could be found between {0} and {1}".format(
                    vnf_src_name, vnf_dst_name)

        LOG.debug("Creating path between {0} and {1}: {2}".format(
            vnf_src_name, vnf_dst_name, path))

        current_hop = src_sw
        switch_inport_nr = src_sw_inport_nr

        # choose free vlan
        cmd = kwargs.get('cmd')
        vlan = None
        if cmd == 'add-flow':
            if kwargs.get('tag'):
                # use pre-defined tag
                vlan = kwargs.get('tag')
            else:
                vlan = self.vlans.pop()

        # store the used vlan tag to identify this chain
        if not kwargs.get('monitor'):
            chain_dict = {}
            chain_dict['vnf_src_name'] = vnf_src_name
            chain_dict['vnf_dst_name'] = vnf_dst_name
            chain_dict['vnf_src_interface'] = vnf_src_interface
            chain_dict['vnf_dst_interface'] = vnf_dst_interface
            chain_dict['tag'] = vlan
            self.installed_chains.append(chain_dict)

        # iterate through the path to install the flow-entries
        for i in range(0, len(path)):
            current_node = self.getNodeByName(current_hop)

            if i < len(path) - 1:
                next_hop = path[i + 1]
            else:
                # last switch reached
                next_hop = vnf_dst_name

            next_node = self.getNodeByName(next_hop)

            if next_hop == vnf_dst_name:
                switch_outport_nr = dst_sw_outport_nr
                LOG.debug("end node reached: {0}".format(vnf_dst_name))
            elif not isinstance(next_node, OVSSwitch):
                LOG.info("Next node: {0} is not a switch".format(next_hop))
                return "Next node: {0} is not a switch".format(next_hop)
            else:
                # take first link between switches by default
                index_edge_out = 0
                switch_outport_nr = self.DCNetwork_graph[current_hop][next_hop][index_edge_out]['src_port_nr']

            # set OpenFlow entry
            if isinstance(current_node, OVSSwitch):
                kwargs['vlan'] = vlan
                kwargs['path'] = path
                kwargs['current_hop'] = current_hop
                kwargs['switch_inport_name'] = src_sw_inport_name
                kwargs['switch_outport_name'] = dst_sw_outport_name
                kwargs['pathindex'] = i

                if self.controller == RemoteController:
                    # set flow entry via ryu rest api
                    self._set_flow_entry_ryu_rest(
                        current_node, switch_inport_nr, switch_outport_nr, **kwargs)
                else:
                    # set flow entry via ovs-ofctl
                    self._set_flow_entry_dpctl(
                        current_node, switch_inport_nr, switch_outport_nr, **kwargs)

            # take first link between switches by default
            if isinstance(next_node, OVSSwitch):
                switch_inport_nr = self.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                current_hop = next_hop

        flow_options = {
            'priority': kwargs.get('priority', DEFAULT_PRIORITY),
            'cookie': kwargs.get('cookie', DEFAULT_COOKIE),
            'vlan': kwargs['vlan'],
            'path': kwargs['path'],
            'match_input': kwargs.get('match')
        }
        flow_options_str = json.dumps(flow_options, indent=1)
        LOG.info("Installed flow rule: ({}:{}) -> ({}:{}) with options: {}"
                 .format(vnf_src_name, vnf_src_interface, vnf_dst_name, vnf_dst_interface, flow_options))
        return "success: {2} between {0} and {1} with options: {3}".format(
            vnf_src_name, vnf_dst_name, cmd, flow_options_str)

    def _set_flow_entry_ryu_rest(
            self, node, switch_inport_nr, switch_outport_nr, **kwargs):
        match = 'in_port=%s' % switch_inport_nr

        cookie = kwargs.get('cookie')
        match_input = kwargs.get('match')
        cmd = kwargs.get('cmd')
        path = kwargs.get('path')
        index = kwargs.get('pathindex')

        vlan = kwargs.get('vlan')
        priority = kwargs.get('priority', DEFAULT_PRIORITY)
        # flag to not set the ovs port vlan tag
        skip_vlan_tag = kwargs.get('skip_vlan_tag')
        # table id to put this flowentry
        table_id = kwargs.get('table_id')
        if not table_id:
            table_id = 0

        s = ','
        if match_input:
            match = s.join([match, match_input])

        flow = {}
        flow['dpid'] = int(node.dpid, 16)

        if cookie:
            flow['cookie'] = int(cookie)
        if priority:
            flow['priority'] = int(priority)

        flow['table_id'] = table_id

        flow['actions'] = []

        # possible Ryu actions, match fields:
        # http://ryu.readthedocs.io/en/latest/app/ofctl_rest.html#add-a-flow-entry
        if cmd == 'add-flow':
            prefix = 'stats/flowentry/add'
            if vlan is not None:
                if index == 0:  # first node
                    # set vlan tag in ovs instance (to isolate E-LANs)
                    if not skip_vlan_tag:
                        in_port_name = kwargs.get('switch_inport_name')
                        self._set_vlan_tag(node, in_port_name, vlan)
                    # set vlan push action if more than 1 switch in the path
                    if len(path) > 1:
                        action = {}
                        # Push a new VLAN tag if a input frame is
                        # non-VLAN-tagged
                        action['type'] = 'PUSH_VLAN'
                        # Ethertype 0x8100(=33024): IEEE 802.1Q VLAN-tagged
                        # frame
                        action['ethertype'] = 33024
                        flow['actions'].append(action)
                        action = {}
                        action['type'] = 'SET_FIELD'
                        action['field'] = 'vlan_vid'
                        # ryu expects the field to be masked
                        action['value'] = vlan | 0x1000
                        flow['actions'].append(action)

                elif index == len(path) - 1:  # last node
                    # set vlan tag in ovs instance (to isolate E-LANs)
                    if not skip_vlan_tag:
                        out_port_name = kwargs.get('switch_outport_name')
                        self._set_vlan_tag(node, out_port_name, vlan)
                    # set vlan pop action if more than 1 switch in the path
                    if len(path) > 1:
                        match += ',dl_vlan=%s' % vlan
                        action = {}
                        action['type'] = 'POP_VLAN'
                        flow['actions'].append(action)

                else:  # middle nodes
                    match += ',dl_vlan=%s' % vlan

            # output action must come last
            action = {}
            action['type'] = 'OUTPUT'
            action['port'] = switch_outport_nr
            flow['actions'].append(action)

        elif cmd == 'del-flows':
            prefix = 'stats/flowentry/delete'

            if cookie:
                # TODO: add cookie_mask as argument
                # need full mask to match complete cookie
                flow['cookie_mask'] = int('0xffffffffffffffff', 16)

            action = {}
            action['type'] = 'OUTPUT'
            action['port'] = switch_outport_nr
            flow['actions'].append(action)

        flow['match'] = self._parse_match(match)
        self.ryu_REST(prefix, data=flow)

    def _set_vlan_tag(self, node, switch_port, tag):
        node.vsctl('set', 'port {0} tag={1}'.format(switch_port, tag))
        LOG.debug("set vlan in switch: {0} in_port: {1} vlan tag: {2}".format(
            node.name, switch_port, tag))

    def _set_flow_entry_dpctl(
            self, node, switch_inport_nr, switch_outport_nr, **kwargs):

        match = 'in_port=%s' % switch_inport_nr

        cookie = kwargs.get('cookie')
        match_input = kwargs.get('match')
        cmd = kwargs.get('cmd')
        path = kwargs.get('path')
        index = kwargs.get('pathindex')
        vlan = kwargs.get('vlan')

        s = ','
        if cookie:
            cookie = 'cookie=%s' % cookie
            match = s.join([cookie, match])
        if match_input:
            match = s.join([match, match_input])
        if cmd == 'add-flow':
            action = 'action=%s' % switch_outport_nr
            if vlan is not None:
                if index == 0:  # first node
                    action = ('action=mod_vlan_vid:%s' % vlan) + \
                        (',output=%s' % switch_outport_nr)
                    match = '-O OpenFlow13 ' + match
                elif index == len(path) - 1:  # last node
                    match += ',dl_vlan=%s' % vlan
                    action = 'action=strip_vlan,output=%s' % switch_outport_nr
                else:  # middle nodes
                    match += ',dl_vlan=%s' % vlan
            ofcmd = s.join([match, action])
        elif cmd == 'del-flows':
            ofcmd = match
        else:
            ofcmd = ''

        node.dpctl(cmd, ofcmd)
        LOG.info("{3} in switch: {0} in_port: {1} out_port: {2}".format(node.name, switch_inport_nr,
                                                                        switch_outport_nr, cmd))

    # start Ryu Openflow controller as Remote Controller for the DCNetwork
    def startRyu(self, learning_switch=True):
        # start Ryu controller with rest-API
        python_install_path = site.getsitepackages()[0]
        # ryu default learning switch
        # ryu_path = python_install_path + '/ryu/app/simple_switch_13.py'
        # custom learning switch that installs a default NORMAL action in the
        # ovs switches
        dir_path = os.path.dirname(os.path.realpath(__file__))
        ryu_path = dir_path + '/son_emu_simple_switch_13.py'
        ryu_path2 = python_install_path + '/ryu/app/ofctl_rest.py'
        # change the default Openflow controller port to 6653 (official IANA-assigned port number), as used by Mininet
        # Ryu still uses 6633 as default
        ryu_option = '--ofp-tcp-listen-port'
        ryu_of_port = '6653'
        ryu_cmd = 'ryu-manager'
        FNULL = open("/tmp/ryu.log", 'w')
        if learning_switch:
            self.ryu_process = Popen(
                [ryu_cmd, ryu_path, ryu_path2, ryu_option, ryu_of_port], stdout=FNULL, stderr=FNULL)
            LOG.debug('starting ryu-controller with {0}'.format(ryu_path))
            LOG.debug('starting ryu-controller with {0}'.format(ryu_path2))
        else:
            # no learning switch, but with rest api
            self.ryu_process = Popen(
                [ryu_cmd, ryu_path2, ryu_option, ryu_of_port], stdout=FNULL, stderr=FNULL)
            LOG.debug('starting ryu-controller with {0}'.format(ryu_path2))
        time.sleep(1)

    def killRyu(self):
        """
        Stop the Ryu controller that might be started by son-emu.
        :return:
        """
        # try it nicely
        if self.ryu_process is not None:
            self.ryu_process.terminate()
            self.ryu_process.kill()
        # ensure its death ;-)
        Popen(['pkill', '-f', 'ryu-manager'])

    def ryu_REST(self, prefix, dpid=None, data=None):

        if dpid:
            url = self.ryu_REST_api + '/' + str(prefix) + '/' + str(dpid)
        else:
            url = self.ryu_REST_api + '/' + str(prefix)
        if data:
            req = self.RyuSession.post(url, json=data)
        else:
            req = self.RyuSession.get(url)

        # do extra logging if status code is not 200 (OK)
        if req.status_code is not requests.codes.ok:
            logging.info(
                'type {0}  encoding: {1} text: {2} headers: {3} history: {4}'.format(req.headers['content-type'],
                                                                                     req.encoding, req.text,
                                                                                     req.headers, req.history))
            LOG.info('url: {0}'.format(str(url)))
            if data:
                LOG.info('POST: {0}'.format(str(data)))
            LOG.info('status: {0} reason: {1}'.format(
                req.status_code, req.reason))

        if 'json' in req.headers['content-type']:
            ret = req.json()
            return ret

        ret = req.text.rstrip()
        return ret

    # need to respect that some match fields must be integers
    # http://ryu.readthedocs.io/en/latest/app/ofctl_rest.html#description-of-match-and-actions

    def _parse_match(self, match):
        matches = match.split(',')
        dict = {}
        for m in matches:
            match = m.split('=')
            if len(match) == 2:
                try:
                    m2 = int(match[1], 0)
                except BaseException:
                    m2 = match[1]

                dict.update({match[0]: m2})
        return dict

    def find_connected_dc_interface(
            self, vnf_src_name, vnf_src_interface=None):

        if vnf_src_interface is None:
            # take first interface by default
            connected_sw = self.DCNetwork_graph.neighbors(vnf_src_name)[0]
            link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
            vnf_src_interface = link_dict[0]['src_port_id']

        for connected_sw in self.DCNetwork_graph.neighbors(vnf_src_name):
            link_dict = self.DCNetwork_graph[vnf_src_name][connected_sw]
            for link in link_dict:
                if (link_dict[link]['src_port_id'] == vnf_src_interface or
                        link_dict[link]['src_port_name'] == vnf_src_interface):
                    # Fix: we might also get interface names, e.g, from a son-emu-cli call
                    # found the right link and connected switch
                    src_sw_inport_name = link_dict[link]['dst_port_name']
                    return src_sw_inport_name
