import logging

LOG = logging.getLogger("dcemulator.sfc")
LOG.setLevel(logging.INFO)


class SFC:

    def __init__(self):
        self.__port_pairs = []
        self.__port_pair_groups = []
        self.__port_chains = []

    def add_port_pair(self, port_pair):
        self.__port_pairs.append(port_pair)

    def add_port_chain(self, port_chain):
        self.__port_chains.append(port_chain)

    def add_port_pair_groups(self, port_pair_group):
        self.__port_pair_groups.append(port_pair_group)

    def delete_port_pair(self):
        print("ha")




class PortChain:
    def __init__(self):
        self.description
        self.PortPairGroups = []


class PortPairGroup:
    def __init__(self, ):
        self.description
        self.port_pairs = []


class PortPair:
    id = 0

    def __init__(self, vnf_src_name, vnf_dst_name, vnf_src_interface, vnf_dst_interface):
        self.vnf_src_name
        self.vnf_dst_name
        self.vnf_src_interface
        self.vnf_dst_interface