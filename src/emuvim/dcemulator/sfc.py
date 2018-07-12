import logging

# This is the sfc-api data model and it is supposed to cover the api definition in
#  src.emuvim.api.rest.sfc_api_endpoint.py

LOG = logging.getLogger("dcemulator.sfc")
LOG.setLevel(logging.INFO)


class SFC:

    def __init__(self):
        self.__port_pairs = []
        self.__port_pair_groups = []
        self.__port_chains = []
        self.__rendered_service_paths = []

    def get_port_pairs(self):
        return self.__port_pairs

    def add_port_pair(self, port_pair):
        self.__port_pairs.append(port_pair)

    def get_port_pair(self, id):
        for port_pair in self.__port_pairs:
            if port_pair.id == id:
                return port_pair

    def delete_port_pair(self, id):
        for port_pair in self.__port_pairs:
            if port_pair.id == id:
                self.__port_pairs.remove(port_pair)
                return
        raise Exception("not found")

    def get_port_pair_groups(self):
        return self.__port_pair_groups

    def add_port_pair_group(self, port_pair_group):
        self.__port_pair_groups.append(port_pair_group)

    def get_port_pair_group(self, id):
        for port_pair_group in self.__port_pair_groups:
            if port_pair_group.id == id:
                return port_pair_group

    def delete_port_pair_group(self, id):
        for port_pair_group in self.__port_pair_groups:
            if port_pair_group.id == id:
                self.__port_pair_groups.remove(port_pair_group)
                return
        raise Exception("not found")

    def get_port_chains(self):
        return self.__port_chains

    def add_port_chain(self, port_chain):
        self.__port_chains.append(port_chain)

    def get_port_chain(self, id):
        for port_chain in self.__port_chains:
            if port_chain.id == id:
                return port_chain

    def delete_port_chain(self, id):
        for port_chain in self.__port_chains:
            if port_chain.id == id:
                self.__port_chains.remove(port_chain)
                return
        raise Exception("not found")


class PortChain:
    id_counter = 0

    def __init__(self, description, port_pair_groups):
        self.id = PortChain.id_counter = PortChain.id_counter + 1
        self.description = description
        self.port_pair_groups = port_pair_groups  # IDs of the PortPairGroup objects
        self.chain_id = None  # link to RSP


class PortPairGroup:
    id_counter = 0

    def __init__(self, description, port_pairs):
        self.id = PortPairGroup.id_counter = PortPairGroup.id_counter + 1
        self.description = description
        self.port_pairs = port_pairs


class PortPair(object):
    id_counter = 0

    def __init__(self, vnf_src_name, vnf_dst_name, vnf_src_interface, vnf_dst_interface):
        self.id = PortPair.id_counter = PortPair.id_counter + 1
        self.vnf_src_name = vnf_src_name
        self.vnf_dst_name = vnf_dst_name
        self.vnf_src_interface = vnf_src_interface
        self.vnf_dst_interface = vnf_dst_interface


class RSP:
    spi_counter = 0

    def __init__(self):
        self.rspis = []
        self.spi = RSP.spi_counter = RSP.spi_counter + 1


class RSPI:
    def __init__(self, si, ovs_sw, ovs_src_port, ovs_src_port_name, ovs_dst_port, ovs_dst_port_name):
        self.si = si
        self.ovs_sw = ovs_sw
        self.ovs_src_port = ovs_src_port
        self.ovs_src_port_name = ovs_src_port_name
        self.ovs_dst_port = ovs_dst_port
        self.ovs_dst_port_name = ovs_dst_port_name
        pass
