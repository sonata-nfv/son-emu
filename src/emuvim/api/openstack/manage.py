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
import threading
import uuid
import networkx as nx
import emuvim.api.openstack.chain_api as chain_api
import json
import random
from emuvim.api.openstack.resources.net import Net
from emuvim.api.openstack.resources.port import Port
from mininet.node import OVSSwitch, RemoteController, Node


class OpenstackManage(object):
    """
    OpenstackManage is a singleton and management component for the emulator.
    It is the brain of the Openstack component and manages everything that is not datacenter specific like
    network chains or load balancers.
    """
    __instance = None

    def __new__(cls):
        if OpenstackManage.__instance is None:
            OpenstackManage.__instance = object.__new__(cls)
        return OpenstackManage.__instance

    def __init__(self, ip="0.0.0.0", port=4000):
        # we are a singleton, only initialize once!
        self.lock = threading.Lock()
        with self.lock:
            if hasattr(self, "init"):
                return
            self.init = True

        self.endpoints = dict()
        self.cookies = set()
        self.cookies.add(0)
        self.ip = ip
        self.port = port
        self._net = None
        # to keep track which src_vnf(input port on the switch) handles a load
        # balancer
        self.lb_flow_cookies = dict()
        self.chain_flow_cookies = dict()

        # for the visualization also store the complete chain data incl. paths
        self.full_chain_data = dict()
        self.full_lb_data = dict()

        # flow groups could be handled for each switch separately, but this global group counter should be easier to
        # debug and to maintain
        self.flow_groups = dict()

        # we want one global chain api. this should not be datacenter
        # dependent!
        self.chain = chain_api.ChainApi(ip, port, self)
        self.thread = threading.Thread(target=self.chain._start_flask, args=())
        self.thread.name = self.chain.__class__
        self.thread.start()

        # floating ip network setup
        self.floating_switch = None
        self.floating_network = None
        self.floating_netmask = "192.168.100.0/24"
        self.floating_nodes = dict()
        self.floating_cookies = dict()
        self.floating_intf = None
        self.floating_links = dict()

    def stop(self):
        self.chain.stop()
        self.thread.join()

    @property
    def net(self):
        return self._net

    @net.setter
    def net(self, value):
        if self._net is None:
            self._net = value
            # create default networks
            self.init_floating_network()
        self._net = value

    def init_floating_network(self, name="default"):
        """
        Initialize the floating network component for the emulator.
        Will not do anything if already initialized.
        """
        if self.net is not None and self.floating_switch is None:
            # create a floating network
            fn = self.floating_network = Net(name)
            fn.id = str(uuid.uuid4())
            fn.set_cidr(self.floating_netmask)

            # create a subnet
            fn.subnet_id = str(uuid.uuid4())
            fn.subnet_name = fn.name + "-sub"

            # create a port for the host
            port = Port("root-port")
            # port.id = str(uuid.uuid4())
            port.net_name = fn.name

            # get next free ip
            root_ip = fn.get_new_ip_address(port.name)
            port.ip_address = root_ip
            # floating ip network setup
            # wierd way of getting a datacenter object
            first_dc = list(self.net.dcs.values())[0]
            # set a dpid for the switch. for this we have to get the id of the
            # next possible dc
            self.floating_switch = self.net.addSwitch(
                "fs1", dpid=hex(first_dc._get_next_dc_dpid())[2:])
            # this is the interface appearing on the physical host
            self.floating_root = Node('root', inNamespace=False)
            self.net.hosts.append(self.floating_root)
            self.net.nameToNode['root'] = self.floating_root
            self.floating_intf = self.net.addLink(
                self.floating_root, self.floating_switch).intf1
            self.floating_root.setIP(root_ip, intf=self.floating_intf)
            self.floating_nodes[(self.floating_root.name,
                                 root_ip)] = self.floating_root

    def stop_floating_network(self):
        self._net = None
        self.floating_switch = None

    def add_endpoint(self, ep):
        """
        Registers an openstack endpoint with manage

        :param ep: Openstack API endpoint
        :type ep: :class:`heat.openstack_api_endpoint`
        """
        key = "%s:%s" % (ep.ip, ep.port)
        self.endpoints[key] = ep

    def get_cookie(self):
        """
        Get an unused cookie.

        :return: Cookie
        :rtype: ``int``
        """
        cookie = int(max(self.cookies) + 1)
        self.cookies.add(cookie)
        return cookie

    def get_flow_group(self, src_vnf_name, src_vnf_interface):
        """
        Gets free group that is not currently used by any other flow for the specified interface / VNF.

        :param src_vnf_name: Source VNF name
        :type src_vnf_name: ``str``
        :param src_vnf_interface: Source VNF interface name
        :type src_vnf_interface: ``str``
        :return: Flow group identifier.
        :rtype: ``int``
        """
        if (src_vnf_name, src_vnf_interface) not in self.flow_groups:
            grp = int(len(self.flow_groups) + 1)
            self.flow_groups[(src_vnf_name, src_vnf_interface)] = grp
        else:
            grp = self.flow_groups[(src_vnf_name, src_vnf_interface)]
        return grp

    def check_vnf_intf_pair(self, vnf_name, vnf_intf_name):
        """
        Checks if a VNF exists and has the given interface

        :param vnf_name: Name of the VNF to be checked
        :type vnf_name: ``str``
        :param vnf_intf_name: Name of the interface that belongst to the VNF
        :type vnf_intf_name: ``str``
        :return: ``True`` if it is valid pair, else ``False``
        :rtype: ``bool``
        """

        if vnf_name in self.net:
            vnf = self.net.getNodeByName(vnf_name)
            return vnf_intf_name in vnf.nameToIntf

    def network_action_start(self, vnf_src_name, vnf_dst_name, **kwargs):
        """
        Starts a network chain for a source destination pair

        :param vnf_src_name: Name of the source VNF
        :type vnf_src_name: ``str``
        :param vnf_dst_name: Name of the source VNF interface
        :type vnf_dst_name: ``str``
        :param \**kwargs: See below

        :Keyword Arguments:
            * *vnf_src_interface* (``str``): Name of source interface.
            * *vnf_dst_interface* (``str``): Name of destination interface.
            * *weight* (``int``): This value is fed into the shortest path computation if no path is specified.
            * *match* (``str``): A custom match entry for the openflow flow rules. Only vlanid or port possible.
            * *bidirectional* (``bool``): If set the chain will be set in both directions, else it will just set up \
                            from source to destination.
            * *cookie* (``int``): Cookie value used by openflow. Used to identify the flows in the switches to be \
                            able to modify the correct flows.
            * *no_route* (``bool``): If set a layer 3 route to the target interface will not be set up.
        :return: The cookie chosen for the flow.
        :rtype: ``int``
        """
        try:
            vnf_src_interface = kwargs.get('vnf_src_interface')
            vnf_dst_interface = kwargs.get('vnf_dst_interface')
            layer2 = kwargs.get('layer2', True)
            match = kwargs.get('match')
            flow = (vnf_src_name, vnf_src_interface,
                    vnf_dst_name, vnf_dst_interface)
            if flow in self.chain_flow_cookies:
                raise Exception(
                    "There is already a chain at the specified src/dst pair!")
            # set up a layer 2 chain, this allows multiple chains for the same
            # interface
            src_node = self.net.getNodeByName(vnf_src_name)
            dst_node = self.net.getNodeByName(vnf_dst_name)
            dst_intf = dst_node.intf(vnf_dst_interface)
            if layer2:
                switch, inport = self._get_connected_switch_data(
                    vnf_src_name, vnf_src_interface)
                self.setup_arp_reply_at(
                    switch, inport, dst_intf.IP(), dst_intf.MAC())
                if isinstance(match, str):
                    match += ",dl_dst=%s" % dst_intf.MAC()
                else:
                    match = "dl_dst=%s" % dst_intf.MAC()

            cookie = kwargs.get('cookie', self.get_cookie())
            self.cookies.add(cookie)
            self.net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=vnf_src_interface,
                vnf_dst_interface=vnf_dst_interface,
                cmd='add-flow',
                weight=kwargs.get('weight'),
                match=match,
                bidirectional=False,
                cookie=cookie,
                path=kwargs.get('path'))

            # to keep this logic seperate of the core son-emu do the
            # housekeeping here
            data = dict()
            data["src_vnf"] = vnf_src_name
            data["src_intf"] = vnf_src_interface
            data["dst_vnf"] = vnf_dst_name
            data["dst_intf"] = vnf_dst_interface
            data["cookie"] = cookie
            data["layer2"] = layer2
            if kwargs.get('path') is not None:
                data["path"] = kwargs.get('path')
            else:
                data["path"] = self._get_path(vnf_src_name, vnf_dst_name, vnf_src_interface,
                                              vnf_dst_interface)[0]

            # add route to dst ip to this interface
            # this might block on containers that are still setting up, so
            # start a new thread
            if not kwargs.get('no_route'):
                # son_emu does not like concurrent commands for a container so we need to lock this if multiple chains
                # on the same interface are created
                src_node.setHostRoute(dst_node.intf(
                    vnf_dst_interface).IP(), vnf_src_interface)

            try:
                son_emu_data = json.loads(
                    self.get_son_emu_chain_data(vnf_src_name))
            except BaseException:
                son_emu_data = dict()
            if "son_emu_data" not in son_emu_data:
                son_emu_data["son_emu_data"] = dict()
            if "interfaces" not in son_emu_data["son_emu_data"]:
                son_emu_data["son_emu_data"]["interfaces"] = dict()
            if vnf_src_interface not in son_emu_data["son_emu_data"]["interfaces"]:
                son_emu_data["son_emu_data"]["interfaces"][vnf_src_interface] = list()
                son_emu_data["son_emu_data"]["interfaces"][vnf_src_interface].append(
                    dst_intf.IP())

            self.set_son_emu_chain_data(vnf_src_name, son_emu_data)

            if kwargs.get('bidirectional', False):
                # call the reverse direction
                path = kwargs.get('path')
                if path is not None:
                    path = list(reversed(path))
                self.network_action_start(vnf_dst_name, vnf_src_name, vnf_src_interface=vnf_dst_interface,
                                          vnf_dst_interface=vnf_src_interface, bidirectional=False,
                                          layer2=kwargs.get('layer2', False), path=path,
                                          no_route=kwargs.get('no_route'))

            self.full_chain_data[flow] = data
            self.chain_flow_cookies[flow] = cookie
            return cookie
        except Exception as ex:
            logging.exception("RPC error.")
            raise Exception(ex.message)

    def network_action_stop(self, vnf_src_name, vnf_dst_name, **kwargs):
        """
        Starts a network chain for a source destination pair

        :param vnf_src_name: Name of the source VNF
        :type vnf_src_name: ``str``
        :param vnf_dst_name: Name of the source VNF interface
        :type vnf_dst_name: ``str``
        :param \**kwargs: See below

        :Keyword Arguments:
            * *vnf_src_interface* (``str``): Name of source interface.
            * *vnf_dst_interface* (``str``): Name of destination interface.
            * *bidirectional* (``bool``): If set the chain will be torn down in both directions, else it will just\
                            be torn down from source to destination.
            * *cookie* (``int``): Cookie value used by openflow. Used to identify the flows in the switches to be \
                            able to modify the correct flows.
        """
        try:
            if 'cookie' in kwargs:
                return self.delete_flow_by_cookie(kwargs.get('cookie'))

            if kwargs.get('bidirectional', False):
                self.delete_chain_by_intf(vnf_dst_name, kwargs.get('vnf_dst_interface'),
                                          vnf_src_name, kwargs.get('vnf_src_interface'))

            return self.delete_chain_by_intf(vnf_src_name, kwargs.get('vnf_src_interface'),
                                             vnf_dst_name, kwargs.get('vnf_dst_interface'))
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def set_son_emu_chain_data(self, vnf_name, data):
        """
        Set son-emu chain data for this node.

        :param vnf_name: The name of the vnf where the data is stored.
        :type vnf_name: ``str``
        :param data: Raw data to store on the node.
        :type data: ``str``
        """
        self.net.getNodeByName(vnf_name).cmd(
            "echo \'%s\' > /tmp/son_emu_data.json" % json.dumps(data))
        ip_list = []
        for intf in data['son_emu_data']['interfaces'].values():
            ip_list.extend(intf)

        self.net.getNodeByName(vnf_name).cmd(
            "echo \'%s\' > /tmp/son_emu_data" % "\n".join(ip_list))

    def get_son_emu_chain_data(self, vnf_name):
        """
        Get the current son-emu chain data set for this node.

        :param vnf_name: The name of the vnf where the data is stored.
        :type vnf_name: ``str``
        :return: raw data stored on the node
        :rtype: ``str``
        """
        return self.net.getNodeByName(vnf_name).cmd(
            "cat /tmp/son_emu_data.json")

    def _get_connected_switch_data(self, vnf_name, vnf_interface):
        """
        Get the switch an interface is connected to
        :param vnf_name: Name of the VNF
        :type vnf_name: ``str``
        :param vnf_interface: Name of the VNF interface
        :type vnf_interface: ``str``
        :return: List containing the switch, and the inport number
        :rtype: [``str``, ``int``]
        """
        src_sw = None
        src_sw_inport_nr = None
        for connected_sw in self.net.DCNetwork_graph.neighbors(vnf_name):
            link_dict = self.net.DCNetwork_graph[vnf_name][connected_sw]
            for link in link_dict:
                if (link_dict[link]['src_port_id'] == vnf_interface or
                    link_dict[link][
                        'src_port_name'] == vnf_interface):
                    # found the right link and connected switch
                    src_sw = connected_sw
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']
                    break

        return src_sw, src_sw_inport_nr

    def _get_path(self, src_vnf, dst_vnf, src_vnf_intf, dst_vnf_intf):
        """
        Own implementation of the get_path function from DCNetwork, because we just want the path and not set up
        flows on the way.

        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param src_vnf_intf: Name of the source VNF interface
        :type src_vnf_intf: ``str``
        :param dst_vnf_intf: Name of the destination VNF interface
        :type dst_vnf_intf: ``str``
        :return: path, src_sw, dst_sw
        :rtype: ``list``, ``str``, ``str``
        """
        # modified version of the _chainAddFlow from
        # emuvim.dcemulator.net._chainAddFlow
        src_sw = None
        dst_sw = None
        logging.debug("Find shortest path from vnf %s to %s",
                      src_vnf, dst_vnf)

        for connected_sw in self.net.DCNetwork_graph.neighbors(src_vnf):
            link_dict = self.net.DCNetwork_graph[src_vnf][connected_sw]
            for link in link_dict:
                if (link_dict[link]['src_port_id'] == src_vnf_intf or
                    link_dict[link][
                        'src_port_name'] == src_vnf_intf):
                    # found the right link and connected switch
                    src_sw = connected_sw
                    break

        for connected_sw in self.net.DCNetwork_graph.neighbors(dst_vnf):
            link_dict = self.net.DCNetwork_graph[connected_sw][dst_vnf]
            for link in link_dict:
                if link_dict[link]['dst_port_id'] == dst_vnf_intf or \
                        link_dict[link][
                        'dst_port_name'] == dst_vnf_intf:
                    # found the right link and connected
                    dst_sw = connected_sw
                    break
        logging.debug("From switch %s to %s " % (src_sw, dst_sw))

        # get shortest path
        try:
            # returns the first found shortest path
            # if all shortest paths are wanted, use: all_shortest_paths
            path = nx.shortest_path(self.net.DCNetwork_graph, src_sw, dst_sw)
        except BaseException:
            logging.exception("No path could be found between {0} and {1} using src_sw={2} and dst_sw={3}".format(
                src_vnf, dst_vnf, src_sw, dst_sw))
            logging.debug("Graph nodes: %r" % self.net.DCNetwork_graph.nodes())
            logging.debug("Graph edges: %r" % self.net.DCNetwork_graph.edges())
            for e, v in self.net.DCNetwork_graph.edges():
                logging.debug("%r" % self.net.DCNetwork_graph[e][v])
            return "No path could be found between {0} and {1}".format(
                src_vnf, dst_vnf)

        logging.info("Shortest path between {0} and {1}: {2}".format(
            src_vnf, dst_vnf, path))
        return path, src_sw, dst_sw

    def add_loadbalancer(self, src_vnf_name, src_vnf_interface, lb_data):
        """
        This function will set up a loadbalancer at the given interface.

        :param src_vnf_name: Name of the source VNF
        :type src_vnf_name: ``str``
        :param src_vnf_interface: Name of the destination VNF
        :type src_vnf_interface: ``str``
        :param lb_data: A dictionary containing the destination data as well as custom path settings
        :type lb_data: ``dict``

        :Example:
         lbdata = {"dst_vnf_interfaces": {"dc2_man_web0": "port-man-2",
         "dc3_man_web0": "port-man-4","dc4_man_web0": "port-man-6"}, "path": {"dc2_man_web0": {"port-man-2": [ "dc1.s1",\
         "s1", "dc2.s1"]}}}
        """
        net = self.net
        src_sw_inport_nr = 0
        src_sw = None
        dest_intfs_mapping = lb_data.get('dst_vnf_interfaces', dict())
        # a custom path can be specified as a list of switches
        custom_paths = lb_data.get('path', dict())
        dest_vnf_outport_nrs = list()

        logging.debug("Call to add_loadbalancer at %s intfs:%s" %
                      (src_vnf_name, src_vnf_interface))

        if not self.check_vnf_intf_pair(src_vnf_name, src_vnf_interface):
            raise Exception(u"Source VNF %s or intfs %s does not exist" % (
                src_vnf_name, src_vnf_interface))

        # find the switch belonging to the source interface, as well as the
        # inport nr
        for connected_sw in net.DCNetwork_graph.neighbors(src_vnf_name):
            link_dict = net.DCNetwork_graph[src_vnf_name][connected_sw]
            for link in link_dict:
                if link_dict[link]['src_port_name'] == src_vnf_interface:
                    src_sw = connected_sw
                    src_sw_inport_nr = link_dict[link]['dst_port_nr']
                    break

        if src_sw is None or src_sw_inport_nr == 0:
            raise Exception(u"Source VNF or interface can not be found.")

        # get all target interface outport numbers
        for vnf_name in dest_intfs_mapping:
            if vnf_name not in net.DCNetwork_graph:
                raise Exception(u"Target VNF %s is not known." % vnf_name)
            for connected_sw in net.DCNetwork_graph.neighbors(vnf_name):
                link_dict = net.DCNetwork_graph[vnf_name][connected_sw]
                for link in link_dict:
                    if link_dict[link]['src_port_name'] == dest_intfs_mapping[vnf_name]:
                        dest_vnf_outport_nrs.append(
                            int(link_dict[link]['dst_port_nr']))
        # get first switch
        if (src_vnf_name, src_vnf_interface) not in self.lb_flow_cookies:
            self.lb_flow_cookies[(src_vnf_name, src_vnf_interface)] = list()

        src_ip = None
        src_mac = None
        for intf in net[src_vnf_name].intfs.values():
            if intf.name == src_vnf_interface:
                src_mac = intf.mac
                src_ip = intf.ip

        # set up paths for each destination vnf individually
        index = 0
        cookie = self.get_cookie()
        main_cmd = "add-flow -OOpenFlow13"
        self.lb_flow_cookies[(src_vnf_name, src_vnf_interface)].append(cookie)

        # bookkeeping
        data = dict()
        data["src_vnf"] = src_vnf_name
        data["src_intf"] = src_vnf_interface
        data["paths"] = list()
        data["cookie"] = cookie

        # lb mac for src -> target connections
        lb_mac = "31:33:70:%02x:%02x:%02x" % (random.randint(
            0, 255), random.randint(0, 255), random.randint(0, 255))

        # calculate lb ip as src_intf.ip +1
        octets = src_ip.split('.')
        octets[3] = str(int(octets[3]) + 1)
        plus_one = '.'.join(octets)

        # set up arp reply as well as add the route to the interface
        self.setup_arp_reply_at(src_sw, src_sw_inport_nr,
                                plus_one, lb_mac, cookie=cookie)
        net.getNodeByName(src_vnf_name).setHostRoute(
            plus_one, src_vnf_interface)

        for dst_vnf_name, dst_vnf_interface in dest_intfs_mapping.items():
            path, src_sw, dst_sw = self._get_path(src_vnf_name, dst_vnf_name,
                                                  src_vnf_interface, dst_vnf_interface)

            # use custom path if one is supplied
            # json does not support hashing on tuples so we use nested dicts
            if custom_paths is not None and dst_vnf_name in custom_paths:
                if dst_vnf_interface in custom_paths[dst_vnf_name]:
                    path = custom_paths[dst_vnf_name][dst_vnf_interface]
                    logging.debug("Taking custom path from %s to %s: %s" % (
                        src_vnf_name, dst_vnf_name, path))

            if not self.check_vnf_intf_pair(dst_vnf_name, dst_vnf_interface):
                self.delete_loadbalancer(src_vnf_name, src_vnf_interface)
                raise Exception(u"VNF %s or intfs %s does not exist" %
                                (dst_vnf_name, dst_vnf_interface))
            if isinstance(path, dict):
                self.delete_loadbalancer(src_vnf_name, src_vnf_interface)
                raise Exception(
                    u"Can not find a valid path. Are you specifying the right interfaces?.")

            target_mac = "fa:17:00:03:13:37"
            target_ip = "0.0.0.0"
            for intf in net[dst_vnf_name].intfs.values():
                if intf.name == dst_vnf_interface:
                    target_mac = str(intf.mac)
                    target_ip = str(intf.ip)
            dst_sw_outport_nr = dest_vnf_outport_nrs[index]
            current_hop = src_sw
            switch_inport_nr = src_sw_inport_nr

            # self.setup_arp_reply_at(src_sw, src_sw_inport_nr, target_ip, target_mac, cookie=cookie)
            net.getNodeByName(dst_vnf_name).setHostRoute(
                src_ip, dst_vnf_interface)

            # choose free vlan if path contains more than 1 switch
            if len(path) > 1:
                vlan = net.vlans.pop()
                if vlan == 0:
                    vlan = net.vlans.pop()
            else:
                vlan = None

            single_flow_data = dict()
            single_flow_data["dst_vnf"] = dst_vnf_name
            single_flow_data["dst_intf"] = dst_vnf_interface
            single_flow_data["path"] = path
            single_flow_data["vlan"] = vlan
            single_flow_data["cookie"] = cookie

            data["paths"].append(single_flow_data)

            # src to target
            for i in range(0, len(path)):
                if i < len(path) - 1:
                    next_hop = path[i + 1]
                else:
                    # last switch reached
                    next_hop = dst_vnf_name
                next_node = net.getNodeByName(next_hop)
                if next_hop == dst_vnf_name:
                    switch_outport_nr = dst_sw_outport_nr
                    logging.info("end node reached: {0}".format(dst_vnf_name))
                elif not isinstance(next_node, OVSSwitch):
                    logging.info(
                        "Next node: {0} is not a switch".format(next_hop))
                    return "Next node: {0} is not a switch".format(next_hop)
                else:
                    # take first link between switches by default
                    index_edge_out = 0
                    switch_outport_nr = net.DCNetwork_graph[current_hop][next_hop][index_edge_out]['src_port_nr']

                cmd = 'priority=1,in_port=%s,cookie=%s' % (
                    switch_inport_nr, cookie)
                cmd_back = 'priority=1,in_port=%s,cookie=%s' % (
                    switch_outport_nr, cookie)
                # if a vlan is picked, the connection is routed through
                # multiple switches
                if vlan is not None:
                    if path.index(current_hop) == 0:  # first node
                        # flow #index set up
                        cmd = 'in_port=%s' % src_sw_inport_nr
                        cmd += ',cookie=%s' % cookie
                        cmd += ',table=%s' % cookie
                        cmd += ',ip'
                        cmd += ',reg1=%s' % index
                        cmd += ',actions='
                        # set vlan id
                        cmd += ',push_vlan:0x8100'
                        masked_vlan = vlan | 0x1000
                        cmd += ',set_field:%s->vlan_vid' % masked_vlan
                        cmd += ',set_field:%s->eth_dst' % target_mac
                        cmd += ',set_field:%s->ip_dst' % target_ip
                        cmd += ',output:%s' % switch_outport_nr

                        # last switch for reverse route
                        # remove any vlan tags
                        cmd_back += ',dl_vlan=%s' % vlan
                        cmd_back += ',actions=pop_vlan,output:%s' % switch_inport_nr
                    elif next_hop == dst_vnf_name:  # last switch
                        # remove any vlan tags
                        cmd += ',dl_vlan=%s' % vlan
                        cmd += ',actions=pop_vlan,output:%s' % switch_outport_nr
                        # set up arp replys at the port so the dst nodes know
                        # the src
                        self.setup_arp_reply_at(
                            current_hop, switch_outport_nr, src_ip, src_mac, cookie=cookie)

                        # reverse route
                        cmd_back = 'in_port=%s' % switch_outport_nr
                        cmd_back += ',cookie=%s' % cookie
                        cmd_back += ',ip'
                        cmd_back += ',actions='
                        cmd_back += 'push_vlan:0x8100'
                        masked_vlan = vlan | 0x1000
                        cmd_back += ',set_field:%s->vlan_vid' % masked_vlan
                        cmd_back += ',set_field:%s->eth_src' % lb_mac
                        cmd_back += ',set_field:%s->ip_src' % plus_one
                        cmd_back += ',output:%s' % switch_inport_nr
                    else:  # middle nodes
                        # if we have a circle in the path we need to specify this, as openflow will ignore the packet
                        # if we just output it on the same port as it came in
                        if switch_inport_nr == switch_outport_nr:
                            cmd += ',dl_vlan=%s,actions=IN_PORT' % (vlan)
                            cmd_back += ',dl_vlan=%s,actions=IN_PORT' % (vlan)
                        else:
                            cmd += ',dl_vlan=%s,actions=output:%s' % (
                                vlan, switch_outport_nr)
                            cmd_back += ',dl_vlan=%s,actions=output:%s' % (
                                vlan, switch_inport_nr)
                # output the packet at the correct outport
                else:
                    cmd = 'in_port=%s' % src_sw_inport_nr
                    cmd += ',cookie=%s' % cookie
                    cmd += ',table=%s' % cookie
                    cmd += ',ip'
                    cmd += ',reg1=%s' % index
                    cmd += ',actions='
                    cmd += ',set_field:%s->eth_dst' % target_mac
                    cmd += ',set_field:%s->ip_dst' % target_ip
                    cmd += ',output:%s' % switch_outport_nr

                    # reverse route
                    cmd_back = 'in_port=%s' % switch_outport_nr
                    cmd_back += ',cookie=%s' % cookie
                    cmd_back += ',ip'
                    cmd_back += ',actions='
                    cmd_back += ',set_field:%s->eth_src' % lb_mac
                    cmd_back += ',set_field:%s->ip_src' % plus_one
                    cmd_back += ',output:%s' % src_sw_inport_nr

                    self.setup_arp_reply_at(
                        current_hop, switch_outport_nr, src_ip, src_mac, cookie=cookie)

                # excecute the command on the target switch
                logging.debug(cmd)
                cmd = "\"%s\"" % cmd
                cmd_back = "\"%s\"" % cmd_back
                net[current_hop].dpctl(main_cmd, cmd)
                net[current_hop].dpctl(main_cmd, cmd_back)

                # set next hop for the next iteration step
                if isinstance(next_node, OVSSwitch):
                    switch_inport_nr = net.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                    current_hop = next_hop

            # advance to next destination
            index += 1

        # set up the actual load balancing rule as a multipath on the very
        # first switch
        cmd = '"in_port=%s' % src_sw_inport_nr
        cmd += ',cookie=%s' % (cookie)
        cmd += ',ip'
        cmd += ',actions='
        # push 0x01 into the first register
        cmd += 'load:0x1->NXM_NX_REG0[]'
        # load balance modulo n over all dest interfaces
        # TODO: in newer openvswitch implementations this should be changed to symmetric_l3l4+udp
        # to balance any kind of traffic
        cmd += ',multipath(symmetric_l4,1024,modulo_n,%s,0,NXM_NX_REG1[0..12])' % len(
            dest_intfs_mapping)
        # reuse the cookie as table entry as it will be unique
        cmd += ',resubmit(, %s)"' % cookie

        # actually add the flow
        logging.debug("Switch: %s, CMD: %s" % (src_sw, cmd))
        net[src_sw].dpctl(main_cmd, cmd)

        # finally add all flow data to the internal data storage
        self.full_lb_data[(src_vnf_name, src_vnf_interface)] = data

    def add_floating_lb(self, datacenter, lb_data):
        """
        This function will set up a loadbalancer at the given datacenter.
        This function returns the floating ip assigned to the loadbalancer as multiple ones are possible.

        :param datacenter: The datacenter entrypoint
        :type datacenter: ``str``
        :param lb_data: A dictionary containing the destination data as well as custom path settings
        :type lb_data: ``dict``

        :Example:
         lbdata = {"dst_vnf_interfaces": {"dc2_man_web0": "port-man-2",
         "dc3_man_web0": "port-man-4","dc4_man_web0": "port-man-6"}, "path": {"dc2_man_web0": {"port-man-2": [ "dc1.s1",\
         "s1", "dc2.s1"]}}}
        """
        net = self.net
        src_sw_inport_nr = 1
        src_sw = self.floating_switch.name
        dest_intfs_mapping = lb_data.get('dst_vnf_interfaces', dict())
        # a custom path can be specified as a list of switches
        custom_paths = lb_data.get('path', dict())
        dest_vnf_outport_nrs = list()

        if datacenter not in self.net.dcs:
            raise Exception(u"Source datacenter can not be found.")

        # get all target interface outport numbers
        for vnf_name in dest_intfs_mapping:
            if vnf_name not in net.DCNetwork_graph:
                raise Exception(u"Target VNF %s is not known." % vnf_name)
            for connected_sw in net.DCNetwork_graph.neighbors(vnf_name):
                link_dict = net.DCNetwork_graph[vnf_name][connected_sw]
                for link in link_dict:
                    if link_dict[link]['src_port_name'] == dest_intfs_mapping[vnf_name]:
                        dest_vnf_outport_nrs.append(
                            int(link_dict[link]['dst_port_nr']))

        if len(dest_vnf_outport_nrs) == 0:
            raise Exception(
                "There are no paths specified for the loadbalancer")
        src_ip = self.floating_intf.IP()
        src_mac = self.floating_intf.MAC()

        # set up paths for each destination vnf individually
        index = 0
        cookie = self.get_cookie()
        main_cmd = "add-flow -OOpenFlow13"
        floating_ip = self.floating_network.get_new_ip_address(
            "floating-ip").split("/")[0]

        for dst_vnf_name, dst_vnf_interface in dest_intfs_mapping.items():
            path = None
            # use custom path if one is supplied
            # json does not support hashing on tuples so we use nested dicts
            if custom_paths is not None and dst_vnf_name in custom_paths:
                if dst_vnf_interface in custom_paths[dst_vnf_name]:
                    path = custom_paths[dst_vnf_name][dst_vnf_interface]
                    logging.debug("Taking custom path to %s: %s" %
                                  (dst_vnf_name, path))
            else:
                if datacenter not in self.floating_links:
                    self.floating_links[datacenter] = \
                        net.addLink(self.floating_switch, datacenter)
                path = \
                    self._get_path(self.floating_root.name, dst_vnf_name,
                                   self.floating_intf.name, dst_vnf_interface)[0]

            if isinstance(path, dict):
                self.delete_flow_by_cookie(cookie)
                raise Exception(
                    u"Can not find a valid path. Are you specifying the right interfaces?.")

            intf = net[dst_vnf_name].nameToIntf[dst_vnf_interface]
            target_mac = str(intf.MAC())
            target_ip = str(intf.IP())
            dst_sw_outport_nr = dest_vnf_outport_nrs[index]
            current_hop = src_sw
            switch_inport_nr = src_sw_inport_nr
            vlan = net.vlans.pop()

            # iterate all switches on the path
            for i in range(0, len(path)):
                if i < len(path) - 1:
                    next_hop = path[i + 1]
                else:
                    # last switch reached
                    next_hop = dst_vnf_name
                next_node = net.getNodeByName(next_hop)

                # sanity checks
                if next_hop == dst_vnf_name:
                    switch_outport_nr = dst_sw_outport_nr
                    logging.info("end node reached: {0}".format(dst_vnf_name))
                elif not isinstance(next_node, OVSSwitch):
                    logging.info(
                        "Next node: {0} is not a switch".format(next_hop))
                    return "Next node: {0} is not a switch".format(next_hop)
                else:
                    # take first link between switches by default
                    index_edge_out = 0
                    switch_outport_nr = net.DCNetwork_graph[current_hop][next_hop][index_edge_out]['src_port_nr']

                # default filters, just overwritten on the first node and last
                # node
                cmd = 'priority=1,in_port=%s,cookie=%s' % (
                    switch_inport_nr, cookie)
                cmd_back = 'priority=1,in_port=%s,cookie=%s' % (
                    switch_outport_nr, cookie)
                if i == 0:  # first node
                    cmd = 'in_port=%s' % src_sw_inport_nr
                    cmd += ',cookie=%s' % cookie
                    cmd += ',table=%s' % cookie
                    cmd += ',ip'
                    cmd += ',ip_dst=%s' % floating_ip
                    cmd += ',reg1=%s' % index
                    cmd += ',actions='
                    # set vlan id
                    cmd += ',push_vlan:0x8100'
                    masked_vlan = vlan | 0x1000
                    cmd += ',set_field:%s->vlan_vid' % masked_vlan
                    cmd += ',set_field:%s->eth_dst' % target_mac
                    cmd += ',set_field:%s->ip_dst' % target_ip
                    cmd += ',output:%s' % switch_outport_nr

                    # last switch for reverse route
                    # remove any vlan tags
                    cmd_back += ',dl_vlan=%s' % vlan
                    cmd_back += ',actions=pop_vlan,output:%s' % switch_inport_nr
                    self.setup_arp_reply_at(
                        current_hop, src_sw_inport_nr, floating_ip, target_mac, cookie=cookie)
                elif next_hop == dst_vnf_name:  # last switch
                    # remove any vlan tags
                    cmd += ',dl_vlan=%s' % vlan
                    cmd += ',actions=pop_vlan,output:%s' % switch_outport_nr
                    # set up arp replys at the port so the dst nodes know the
                    # src
                    self.setup_arp_reply_at(
                        current_hop, switch_outport_nr, src_ip, src_mac, cookie=cookie)

                    # reverse route
                    cmd_back = 'in_port=%s' % switch_outport_nr
                    cmd_back += ',cookie=%s' % cookie
                    cmd_back += ',ip'
                    cmd_back += ',actions='
                    cmd_back += 'push_vlan:0x8100'
                    masked_vlan = vlan | 0x1000
                    cmd_back += ',set_field:%s->vlan_vid' % masked_vlan
                    cmd_back += ',set_field:%s->eth_src' % src_mac
                    cmd_back += ',set_field:%s->ip_src' % floating_ip
                    cmd_back += ',output:%s' % switch_inport_nr
                    net.getNodeByName(dst_vnf_name).setHostRoute(
                        src_ip, dst_vnf_interface)
                else:  # middle node
                    # if we have a circle in the path we need to specify this, as openflow will ignore the packet
                    # if we just output it on the same port as it came in
                    if switch_inport_nr == switch_outport_nr:
                        cmd += ',dl_vlan=%s,actions=IN_PORT' % (vlan)
                        cmd_back += ',dl_vlan=%s,actions=IN_PORT' % (vlan)
                    else:
                        cmd += ',dl_vlan=%s,actions=output:%s' % (
                            vlan, switch_outport_nr)
                        cmd_back += ',dl_vlan=%s,actions=output:%s' % (
                            vlan, switch_inport_nr)

                # excecute the command on the target switch
                logging.debug(cmd)
                cmd = "\"%s\"" % cmd
                cmd_back = "\"%s\"" % cmd_back
                net[current_hop].dpctl(main_cmd, cmd)
                net[current_hop].dpctl(main_cmd, cmd_back)

                # set next hop for the next iteration step
                if isinstance(next_node, OVSSwitch):
                    switch_inport_nr = net.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                    current_hop = next_hop

            # advance to next destination
            index += 1

        # set up the actual load balancing rule as a multipath on the very
        # first switch
        cmd = '"in_port=%s' % src_sw_inport_nr
        cmd += ',cookie=%s' % (cookie)
        cmd += ',ip'
        cmd += ',actions='
        # push 0x01 into the first register
        cmd += 'load:0x1->NXM_NX_REG0[]'
        # load balance modulo n over all dest interfaces
        # TODO: in newer openvswitch implementations this should be changed to symmetric_l3l4+udp
        # to balance any kind of traffic
        cmd += ',multipath(symmetric_l4,1024,modulo_n,%s,0,NXM_NX_REG1[0..12])' % len(
            dest_intfs_mapping)
        # reuse the cookie as table entry as it will be unique
        cmd += ',resubmit(, %s)"' % cookie

        # actually add the flow
        logging.debug("Switch: %s, CMD: %s" % (src_sw, cmd))
        net[src_sw].dpctl(main_cmd, cmd)

        self.floating_cookies[cookie] = floating_ip

        return cookie, floating_ip

    def setup_arp_reply_at(self, switch, port_nr,
                           target_ip, target_mac, cookie=None):
        """
        Sets up a custom ARP reply at a switch.
        An ARP request coming in on the `port_nr` for `target_ip` will be answered with target IP/MAC.

        :param switch: The switch belonging to the interface
        :type switch: ``str``
        :param port_nr: The port number at the switch that is connected to the interface
        :type port_nr: ``int``
        :param target_ip: The IP for which to set up the ARP reply
        :type target_ip: ``str``
        :param target_mac: The MAC address of the target interface
        :type target_mac: ``str``
        :param cookie: cookie to identify the ARP request, if None a new one will be picked
        :type cookie: ``int`` or ``None``
        :return: cookie
        :rtype: ``int``
        """
        if cookie is None:
            cookie = self.get_cookie()
        main_cmd = "add-flow -OOpenFlow13"

        # first set up ARP requests for the source node, so it will always
        # 'find' a partner
        cmd = '"in_port=%s' % port_nr
        cmd += ',cookie=%s' % cookie
        cmd += ',arp'
        # only answer for target ip arp requests
        cmd += ',arp_tpa=%s' % target_ip
        cmd += ',actions='
        # set message type to ARP reply
        cmd += 'load:0x2->NXM_OF_ARP_OP[]'
        # set src ip as dst ip
        cmd += ',move:NXM_OF_ETH_SRC[]->NXM_OF_ETH_DST[]'
        # set src mac
        cmd += ',set_field:%s->eth_src' % target_mac
        # set src as target
        cmd += ',move:NXM_NX_ARP_SHA[]->NXM_NX_ARP_THA[], move:NXM_OF_ARP_SPA[]->NXM_OF_ARP_TPA[]'
        # set target mac as hex
        cmd += ',load:0x%s->NXM_NX_ARP_SHA[]' % "".join(target_mac.split(':'))
        # set target ip as hex
        octets = target_ip.split('.')
        dst_ip_hex = '{:02X}{:02X}{:02X}{:02X}'.format(*map(int, octets))
        cmd += ',load:0x%s->NXM_OF_ARP_SPA[]' % dst_ip_hex
        # output to incoming port remember the closing "
        cmd += ',IN_PORT"'
        self.net[switch].dpctl(main_cmd, cmd)
        logging.debug(
            "Set up ARP reply at %s port %s." % (switch, port_nr))

    def delete_flow_by_cookie(self, cookie):
        """
        Removes a flow identified by the cookie

        :param cookie: The cookie for the specified flow
        :type cookie: ``int``
        :return: True if successful, else false
        :rtype: ``bool``
        """
        if not cookie:
            return False
        logging.debug("Deleting flow by cookie %d" % (cookie))
        flows = list()
        # we have to call delete-group for each switch
        for node in self.net.switches:
            flow = dict()
            flow["dpid"] = int(node.dpid, 16)
            flow["cookie"] = cookie
            flow['cookie_mask'] = int('0xffffffffffffffff', 16)

            flows.append(flow)
        for flow in flows:
            logging.debug("Deleting flowentry with cookie %d" % (
                flow["cookie"]))
            if self.net.controller == RemoteController:
                self.net.ryu_REST('stats/flowentry/delete', data=flow)

        self.cookies.remove(cookie)
        return True

    def delete_chain_by_intf(
            self, src_vnf_name, src_vnf_intf, dst_vnf_name, dst_vnf_intf):
        """
        Removes a flow identified by the vnf_name/vnf_intf pairs

        :param src_vnf_name: The vnf name for the specified flow
        :type src_vnf_name: ``str``
        :param src_vnf_intf: The interface name for the specified flow
        :type src_vnf_intf: ``str``
        :param dst_vnf_name: The vnf name for the specified flow
        :type dst_vnf_name: ``str``
        :param dst_vnf_intf: The interface name for the specified flow
        :type dst_vnf_intf: ``str``
        :return: True if successful, else false
        :rtype: ``bool``
        """
        logging.debug("Deleting flow for vnf/intf pair %s %s" %
                      (src_vnf_name, src_vnf_intf))
        if not self.check_vnf_intf_pair(src_vnf_name, src_vnf_intf):
            return False
        if not self.check_vnf_intf_pair(dst_vnf_name, dst_vnf_intf):
            return False
        target_flow = (src_vnf_name, src_vnf_intf, dst_vnf_name, dst_vnf_intf)
        if target_flow not in self.chain_flow_cookies:
            return False

        success = self.delete_flow_by_cookie(
            self.chain_flow_cookies[target_flow])

        if success:
            del self.chain_flow_cookies[target_flow]
            del self.full_chain_data[target_flow]
            return True
        return False

    def delete_loadbalancer(self, vnf_src_name, vnf_src_interface):
        '''
        Removes a loadbalancer that is configured for the node and interface

        :param src_vnf_name: Name of the source VNF
        :param src_vnf_interface: Name of the destination VNF
        '''
        flows = list()
        # we have to call delete-group for each switch
        delete_group = list()
        group_id = self.get_flow_group(vnf_src_name, vnf_src_interface)
        for node in self.net.switches:
            for cookie in self.lb_flow_cookies[(
                    vnf_src_name, vnf_src_interface)]:
                flow = dict()
                flow["dpid"] = int(node.dpid, 16)
                flow["cookie"] = cookie
                flow['cookie_mask'] = int('0xffffffffffffffff', 16)

                flows.append(flow)
            group_del = dict()
            group_del["dpid"] = int(node.dpid, 16)
            group_del["group_id"] = group_id
            delete_group.append(group_del)

        for flow in flows:
            logging.debug("Deleting flowentry with cookie %d belonging to lb at %s:%s" % (
                flow["cookie"], vnf_src_name, vnf_src_interface))
            if self.net.controller == RemoteController:
                self.net.ryu_REST('stats/flowentry/delete', data=flow)

        logging.debug("Deleting group with id %s" % group_id)
        for switch_del_group in delete_group:
            if self.net.controller == RemoteController:
                self.net.ryu_REST("stats/groupentry/delete",
                                  data=switch_del_group)

        # unmap groupid from the interface
        target_pair = (vnf_src_name, vnf_src_interface)
        if target_pair in self.flow_groups:
            del self.flow_groups[target_pair]
        if target_pair in self.full_lb_data:
            del self.full_lb_data[target_pair]

    def delete_floating_lb(self, cookie):
        """
        Delete a floating loadbalancer.
        Floating loadbalancers are different from normal ones as there are multiple ones on the same interface.
        :param cookie: The cookie of the loadbalancer
        :type cookie: ``int``
        """
        cookie = int(cookie)
        if cookie not in self.floating_cookies:
            raise Exception(
                "Can not delete floating loadbalancer as the flowcookie is not known")

        self.delete_flow_by_cookie(cookie)
        floating_ip = self.floating_cookies[cookie]
        self.floating_network.withdraw_ip_address(floating_ip)

    def set_arp_entry(self, vnf_name, vnf_interface, ip, mac):
        """
        Sets an arp entry on the specified VNF. This is done on the node directly and not by open vswitch!
        :param vnf_name: Name of the VNF
        :type vnf_name: ``str``
        :param vnf_interface: Name of the interface
        :type vnf_interface: ``str``
        :param ip: IP to reply to
        :type ip: ``str``
        :param mac: Answer with this MAC
        :type mac: ``str``
        """
        node = self.net.getNodeByName(vnf_name)
        node.cmd("arp -i %s -s %s %s" % (vnf_interface, ip, mac))
