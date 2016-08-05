"""
Copyright (c) 2015 SONATA-NFV and Paderborn University
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
import logging

import site
import time
from subprocess import Popen
import os
import re
import urllib2
from functools import partial

from mininet.net import Containernet
from mininet.node import Controller, DefaultController, OVSSwitch, OVSKernelSwitch, Docker, RemoteController
from mininet.cli import CLI
from mininet.link import TCLink
from mininet.clean import cleanup
import networkx as nx
from emuvim.dcemulator.monitoring import DCNetworkMonitor
from emuvim.dcemulator.node import Datacenter, EmulatorCompute
from emuvim.dcemulator.resourcemodel import ResourceModelRegistrar

LOG = logging.getLogger("dcemulator.net")
LOG.setLevel(logging.DEBUG)

class DCNetwork(Containernet):
    """
    Wraps the original Mininet/Containernet class and provides
    methods to add data centers, switches, etc.

    This class is used by topology definition scripts.
    """

    def __init__(self, controller=RemoteController, monitor=False,
                 enable_learning = True,   # in case of RemoteController (Ryu), learning switch behavior can be turned off/on
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

        # always cleanup environment before we start the emulator
        self.killRyu()
        cleanup()

        # call original Docker.__init__ and setup default controller
        Containernet.__init__(
            self, switch=OVSKernelSwitch, controller=controller, **kwargs)

        # Ryu management
        if controller == RemoteController:
            # start Ryu controller
            self.startRyu(learning_switch=enable_learning)

        # add the specified controller
        self.addController('c0', controller=controller)

        # graph of the complete DC network
        self.DCNetwork_graph = nx.MultiDiGraph()

        # initialize pool of vlan tags to setup the SDN paths
        self.vlans = range(4096)[::-1]

        # link to Ryu REST_API
        ryu_ip = '0.0.0.0'
        ryu_port = '8080'
        self.ryu_REST_api = 'http://{0}:{1}'.format(ryu_ip, ryu_port)

        # monitoring agent
        if monitor:
            self.monitor_agent = DCNetworkMonitor(self)
        else:
            self.monitor_agent = None

        # initialize resource model registrar
        self.rm_registrar = ResourceModelRegistrar(
            dc_emulation_max_cpu, dc_emulation_max_mem)

    def addDatacenter(self, label, metadata={}, resource_log_path=None):
        """
        Create and add a logical cloud data center to the network.
        """
        if label in self.dcs:
            raise Exception("Data center label already exists: %s" % label)
        dc = Datacenter(label, metadata=metadata, resource_log_path=resource_log_path)
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
        LOG.debug("addLink: n1=%s n2=%s" % (str(node1), str(node2)))
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
            if "params1" not in params:
                params["params1"] = {}
            if "ip" not in params["params1"]:
                params["params1"]["ip"] = self.getNextIp()
        if isinstance( node2, Docker ):
            if "params2" not in params:
                params["params2"] = {}
            if "ip" not in params["params2"]:
                params["params2"]["ip"] = self.getNextIp()
        # ensure that we allow TCLinks between data centers
        # TODO this is not optimal, we use cls=Link for containers and TCLink for data centers
        # see Containernet issue: https://github.com/mpeuster/containernet/issues/3
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
            match = re.search('([0-9]*\.?[0-9]+)', params[attr])
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
        self.DCNetwork_graph.add_edge(node1.name, node2.name, attr_dict=attr_dict2)

        attr_dict2 = {'src_port_id': node2_port_id, 'src_port_nr': node2.ports[link.intf2],
                      'src_port_name': node2_port_name,
                     'dst_port_id': node1_port_id, 'dst_port_nr': node1.ports[link.intf1],
                      'dst_port_name': node1_port_name}
        attr_dict2.update(attr_dict)
        self.DCNetwork_graph.add_edge(node2.name, node1.name, attr_dict=attr_dict2)

        return link

    def addDocker( self, label, **params ):
        """
        Wrapper for addDocker method to use custom container class.
        """
        self.DCNetwork_graph.add_node(label)
        return Containernet.addDocker(self, label, cls=EmulatorCompute, **params)

    def removeDocker( self, label, **params ):
        """
        Wrapper for removeDocker method to update graph.
        """
        self.DCNetwork_graph.remove_node(label)
        return Containernet.removeDocker(self, label, **params)

    def addSwitch( self, name, add_to_graph=True, **params ):
        """
        Wrapper for addSwitch method to store switch also in graph.
        """
        if add_to_graph:
            self.DCNetwork_graph.add_node(name)
        return Containernet.addSwitch(self, name, protocols='OpenFlow10,OpenFlow12,OpenFlow13', **params)

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

    # to remove chain do setChain( src, dst, cmd='del-flows')
    def setChain(self, vnf_src_name, vnf_dst_name, vnf_src_interface=None, vnf_dst_interface=None, **kwargs):
        cmd = kwargs.get('cmd')
        if cmd == 'add-flow':
            ret = self._chainAddFlow(vnf_src_name, vnf_dst_name, vnf_src_interface, vnf_dst_interface, **kwargs)
            if kwargs.get('bidirectional'):
                ret = ret +'\n' + self._chainAddFlow(vnf_dst_name, vnf_src_name, vnf_dst_interface, vnf_src_interface, **kwargs)

        elif cmd == 'del-flows':
            ret = self._chainAddFlow(vnf_src_name, vnf_dst_name, vnf_src_interface, vnf_dst_interface, **kwargs)
            if kwargs.get('bidirectional'):
                ret = ret + '\n' + self._chainAddFlow(vnf_dst_name, vnf_src_name, vnf_dst_interface, vnf_src_interface, **kwargs)

        else:
            ret = "Command unknown"

        return ret


    def _chainAddFlow(self, vnf_src_name, vnf_dst_name, vnf_src_interface=None, vnf_dst_interface=None, **kwargs):

        src_sw = None
        dst_sw = None
        src_sw_inport_nr = 0
        dst_sw_outport_nr = 0

        LOG.debug("call chainAddFlow vnf_src_name=%r, vnf_src_interface=%r, vnf_dst_name=%r, vnf_dst_interface=%r",
                  vnf_src_name, vnf_src_interface, vnf_dst_name, vnf_dst_interface)

        #check if port is specified (vnf:port)
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
                    break


        # get shortest path
        try:
            # returns the first found shortest path
            # if all shortest paths are wanted, use: all_shortest_paths
            path = nx.shortest_path(self.DCNetwork_graph, src_sw, dst_sw, weight=kwargs.get('weight'))
        except:
            LOG.exception("No path could be found between {0} and {1} using src_sw={2} and dst_sw={3}".format(
                vnf_src_name, vnf_dst_name, src_sw, dst_sw))
            LOG.debug("Graph nodes: %r" % self.DCNetwork_graph.nodes())
            LOG.debug("Graph edges: %r" % self.DCNetwork_graph.edges())
            for e, v in self.DCNetwork_graph.edges():
                LOG.debug("%r" % self.DCNetwork_graph[e][v])
            return "No path could be found between {0} and {1}".format(vnf_src_name, vnf_dst_name)

        LOG.info("Path between {0} and {1}: {2}".format(vnf_src_name, vnf_dst_name, path))

        current_hop = src_sw
        switch_inport_nr = src_sw_inport_nr

        # choose free vlan if path contains more than 1 switch
        cmd = kwargs.get('cmd')
        vlan = None
        if cmd == 'add-flow':
            if len(path) > 1:
                vlan = self.vlans.pop()

        for i in range(0,len(path)):
            current_node = self.getNodeByName(current_hop)

            if path.index(current_hop) < len(path)-1:
                next_hop = path[path.index(current_hop)+1]
            else:
                #last switch reached
                next_hop = vnf_dst_name

            next_node = self.getNodeByName(next_hop)

            if next_hop == vnf_dst_name:
                switch_outport_nr = dst_sw_outport_nr
                LOG.info("end node reached: {0}".format(vnf_dst_name))
            elif not isinstance( next_node, OVSSwitch ):
                LOG.info("Next node: {0} is not a switch".format(next_hop))
                return "Next node: {0} is not a switch".format(next_hop)
            else:
                # take first link between switches by default
                index_edge_out = 0
                switch_outport_nr = self.DCNetwork_graph[current_hop][next_hop][index_edge_out]['src_port_nr']


           # set of entry via ovs-ofctl
            if isinstance( current_node, OVSSwitch ):
                kwargs['vlan'] = vlan
                kwargs['path'] = path
                kwargs['current_hop'] = current_hop

                if self.controller == RemoteController:
                    ## set flow entry via ryu rest api
                    self._set_flow_entry_ryu_rest(current_node, switch_inport_nr, switch_outport_nr, **kwargs)
                else:
                    ## set flow entry via ovs-ofctl
                    self._set_flow_entry_dpctl(current_node, switch_inport_nr, switch_outport_nr, **kwargs)



            # take first link between switches by default
            if isinstance( next_node, OVSSwitch ):
                switch_inport_nr = self.DCNetwork_graph[current_hop][next_hop][0]['dst_port_nr']
                current_hop = next_hop

        return "path {2} between {0} and {1}".format(vnf_src_name, vnf_dst_name, cmd)

    def _set_flow_entry_ryu_rest(self, node, switch_inport_nr, switch_outport_nr, **kwargs):
        match = 'in_port=%s' % switch_inport_nr

        cookie = kwargs.get('cookie')
        match_input = kwargs.get('match')
        cmd = kwargs.get('cmd')
        path = kwargs.get('path')
        current_hop = kwargs.get('current_hop')
        vlan = kwargs.get('vlan')
        priority = kwargs.get('priority')

        s = ','
        if match_input:
            match = s.join([match, match_input])

        flow = {}
        flow['dpid'] = int(node.dpid, 16)

        if cookie:
            flow['cookie'] = int(cookie)
        if priority:
            flow['priority'] = int(priority)

        flow['actions'] = []

        # possible Ryu actions, match fields:
        # http://ryu.readthedocs.io/en/latest/app/ofctl_rest.html#add-a-flow-entry
        if cmd == 'add-flow':
            prefix = 'stats/flowentry/add'
            if vlan != None:
                if path.index(current_hop) == 0:  # first node
                    action = {}
                    action['type'] = 'PUSH_VLAN'  # Push a new VLAN tag if a input frame is non-VLAN-tagged
                    action['ethertype'] = 33024   # Ethertype 0x8100(=33024): IEEE 802.1Q VLAN-tagged frame
                    flow['actions'].append(action)
                    action = {}
                    action['type'] = 'SET_FIELD'
                    action['field'] = 'vlan_vid'
                    action['value'] = vlan
                    flow['actions'].append(action)
                elif path.index(current_hop) == len(path) - 1:  # last node
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
                flow['cookie_mask'] = int('0xffffffffffffffff', 16)  # need full mask to match complete cookie

            action = {}
            action['type'] = 'OUTPUT'
            action['port'] = switch_outport_nr
            flow['actions'].append(action)

        flow['match'] = self._parse_match(match)
        self.ryu_REST(prefix, data=flow)

    def _set_flow_entry_dpctl(self, node, switch_inport_nr, switch_outport_nr, **kwargs):
        match = 'in_port=%s' % switch_inport_nr

        cookie = kwargs.get('cookie')
        match_input = kwargs.get('match')
        cmd = kwargs.get('cmd')
        path = kwargs.get('path')
        current_hop = kwargs.get('current_hop')
        vlan = kwargs.get('vlan')

        s = ','
        if cookie:
            cookie = 'cookie=%s' % cookie
            match = s.join([cookie, match])
        if match_input:
            match = s.join([match, match_input])
        if cmd == 'add-flow':
            action = 'action=%s' % switch_outport_nr
            if vlan != None:
                if path.index(current_hop) == 0:  # first node
                    action = ('action=mod_vlan_vid:%s' % vlan) + (',output=%s' % switch_outport_nr)
                    match = '-O OpenFlow13 ' + match
                elif path.index(current_hop) == len(path) - 1:  # last node
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
        ryu_path = python_install_path + '/ryu/app/simple_switch_13.py'
        ryu_path2 = python_install_path + '/ryu/app/ofctl_rest.py'
        # change the default Openflow controller port to 6653 (official IANA-assigned port number), as used by Mininet
        # Ryu still uses 6633 as default
        ryu_option = '--ofp-tcp-listen-port'
        ryu_of_port = '6653'
        ryu_cmd = 'ryu-manager'
        FNULL = open("/tmp/ryu.log", 'w')
        if learning_switch:
            self.ryu_process = Popen([ryu_cmd, ryu_path, ryu_path2, ryu_option, ryu_of_port], stdout=FNULL, stderr=FNULL)
        else:
            # no learning switch, but with rest api
            self.ryu_process = Popen([ryu_cmd, ryu_path2, ryu_option, ryu_of_port], stdout=FNULL, stderr=FNULL)
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
        try:
            if dpid:
                url = self.ryu_REST_api + '/' + str(prefix) + '/' + str(dpid)
            else:
                url = self.ryu_REST_api + '/' + str(prefix)
            if data:
                #LOG.info('POST: {0}'.format(str(data)))
                req = urllib2.Request(url, str(data))
            else:
                req = urllib2.Request(url)

            ret = urllib2.urlopen(req).read()
            return ret
        except:
            LOG.info('error url: {0}'.format(str(url)))
            if data: LOG.info('error POST: {0}'.format(str(data)))

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
                except:
                    m2 = match[1]

                dict.update({match[0]:m2})
        return dict

