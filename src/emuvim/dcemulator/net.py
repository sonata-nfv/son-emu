"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""
import logging

import site
from subprocess import Popen
import os

from mininet.net import Dockernet
from mininet.node import Controller, OVSSwitch, OVSKernelSwitch, Switch, Docker, Host, RemoteController
from mininet.cli import CLI
from mininet.log import setLogLevel, info, debug
from mininet.link import TCLink
import networkx as nx
from emuvim.dcemulator.monitoring import DCNetworkMonitor
from emuvim.dcemulator.node import Datacenter, EmulatorCompute
from emuvim.dcemulator.resourcemodel import ResourceModelRegistrar


class DCNetwork(Dockernet):
    """
    Wraps the original Mininet/Dockernet class and provides
    methods to add data centers, switches, etc.

    This class is used by topology definition scripts.
    """

    def __init__(self, dc_emulation_max_cpu=1.0, **kwargs):
        """
        Create an extended version of a Dockernet network
        :param dc_emulation_max_cpu: max. CPU time used by containers in data centers
        :param kwargs: path through for Mininet parameters
        :return:
        """
        self.dcs = {}

        # call original Docker.__init__ and setup default controller
        Dockernet.__init__(
            self, controller=RemoteController, switch=OVSKernelSwitch, **kwargs)

        # ass a remote controller to be able to use Ryu
        self.addController('c0', controller=RemoteController)

        # graph of the complete DC network
        self.DCNetwork_graph=nx.DiGraph()

        # monitoring agent
        self.monitor_agent = DCNetworkMonitor(self)

        # start Ryu controller
        self.startRyu()

        # initialize resource model registrar
        self.rm_registrar = ResourceModelRegistrar(dc_emulation_max_cpu)

    def addDatacenter(self, label, metadata={}):
        """
        Create and add a logical cloud data center to the network.
        """
        if label in self.dcs:
            raise Exception("Data center label already exists: %s" % label)
        dc = Datacenter(label, metadata=metadata)
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
        # see Dockernet issue: https://github.com/mpeuster/dockernet/issues/3
        if "cls" not in params:
            params["cls"] = TCLink

        link = Dockernet.addLink(self, node1, node2, **params)

        # add edge and assigned port number to graph in both directions between node1 and node2
        self.DCNetwork_graph.add_edge(node1.name, node2.name, \
                                      {'src_port': node1.ports[link.intf1], 'dst_port': node2.ports[link.intf2]})
        self.DCNetwork_graph.add_edge(node2.name, node1.name, \
                                       {'src_port': node2.ports[link.intf2], 'dst_port': node1.ports[link.intf1]})

        return link

    def addDocker( self, label, **params ):
        """
        Wrapper for addDocker method to use custom container class.
        """
        self.DCNetwork_graph.add_node(label)
        return Dockernet.addDocker(self, label, cls=EmulatorCompute, **params)

    def removeDocker( self, label, **params ):
        """
        Wrapper for removeDocker method to update graph.
        """
        self.DCNetwork_graph.remove_node(label)
        return Dockernet.removeDocker(self, label, **params)

    def addSwitch( self, name, add_to_graph=True, **params ):
        """
        Wrapper for addSwitch method to store switch also in graph.
        """
        if add_to_graph:
            self.DCNetwork_graph.add_node(name)
        return Dockernet.addSwitch(self, name, protocols='OpenFlow10,OpenFlow12,OpenFlow13', **params)

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
        # stop Ryu controller
        self.ryu_process.terminate()
        #self.ryu_process.kill()
        Dockernet.stop(self)

    def CLI(self):
        CLI(self)

    # to remove chain do setChain( src, dst, cmd='del-flows')
    def setChain(self, vnf_src_name, vnf_dst_name, cmd='add-flow'):
        # get shortest path
        path = nx.shortest_path(self.DCNetwork_graph, vnf_src_name, vnf_dst_name)
        logging.info("Path between {0} and {1}: {2}".format(vnf_src_name, vnf_dst_name, path))

        current_hop = vnf_src_name
        for i in range(0,len(path)):
            next_hop = path[path.index(current_hop)+1]
            next_node = self.getNodeByName(next_hop)

            if next_hop == vnf_dst_name:
                return "path added between {0} and {1}".format(vnf_src_name, vnf_dst_name)
            elif not isinstance( next_node, OVSSwitch ):
                logging.info("Next node: {0} is not a switch".format(next_hop))
                return "Next node: {0} is not a switch".format(next_hop)


            switch_inport = self.DCNetwork_graph[current_hop][next_hop]['dst_port']
            next2_hop = path[path.index(current_hop)+2]
            switch_outport = self.DCNetwork_graph[next_hop][next2_hop]['src_port']

            logging.info("add flow in switch: {0} in_port: {1} out_port: {2}".format(next_node.name, switch_inport, switch_outport))
            # set of entry via ovs-ofctl
            # TODO use rest API of ryu to set flow entries to correct witch dpid
            if isinstance( next_node, OVSSwitch ):
                match = 'in_port=%s' % switch_inport

                if cmd=='add-flow':
                    action = 'action=%s' % switch_outport
                    s = ','
                    ofcmd = s.join([match,action])
                elif cmd=='del-flows':
                    ofcmd = match
                else:
                    ofcmd=''

                next_node.dpctl(cmd, ofcmd)

            current_hop = next_hop

        return "destination node: {0} not reached".format(vnf_dst_name)

    # start Ryu Openflow controller as Remote Controller for the DCNetwork
    def startRyu(self):
        # start Ryu controller with rest-API
        python_install_path = site.getsitepackages()[0]
        ryu_path = python_install_path + '/ryu/app/simple_switch_13.py'
        ryu_path2 =  python_install_path + '/ryu/app/ofctl_rest.py'
        # change the default Openflow controller port to 6653 (official IANA-assigned port number), as used by Mininet
        # Ryu still uses 6633 as default
        ryu_option = '--ofp-tcp-listen-port'
        ryu_of_port = '6653'
        ryu_cmd =  'ryu-manager'
        FNULL = open(os.devnull, 'w')
        self.ryu_process = Popen([ryu_cmd, ryu_path, ryu_path2, ryu_option, ryu_of_port], stdout=FNULL, stderr=FNULL)