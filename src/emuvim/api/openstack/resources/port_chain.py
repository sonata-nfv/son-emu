import random
import uuid
import logging


class PortChain(object):
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.tenant_id = "abcdefghijklmnopqrstuvwxyz123456"
        self.name = name
        self.description = ""
        self.port_pair_groups = list()
        self.flow_classifiers = list()
        self.chain_parameters = dict()

        # Cookie for internal identification of installed flows (e.g. to delete them)
        self.cookie = random.randint(1, 0xffffffff)

    def create_dict(self, compute):
        representation = {
            "name": self.name,
            "tenant_id": self.tenant_id,
            "description": self.description,
            "flow_classifiers": self.flow_classifiers,
            "port_pair_groups": self.port_pair_groups,
            "id": self.id
        }
        return representation

    def install(self, compute):
        for flow_classifier_id in self.flow_classifiers:
            flow_classifier = compute.find_flow_classifier_by_name_or_id(flow_classifier_id)
            if flow_classifier:
                pass
                # TODO: for every flow classifier create match and pass it to setChain

        for group_id in self.port_pair_groups:
            port_pair_group = compute.find_port_pair_group_by_name_or_id(group_id)
            for port_pair_id in port_pair_group.port_pairs:
                port_pair = compute.find_port_pair_by_name_or_id(port_pair_id)

                server_ingress = None
                server_egress = None
                for server in compute.computeUnits.values():
                    if port_pair.ingress.name in server.port_names:
                        server_ingress = server
                    elif port_pair.egress.name in server.port_names:
                        server_egress = server

                # TODO: Not sure, if this should throw an error
                if not server_ingress:
                    logging.warn("Neutron SFC: ingress port %s not connected." % str(port_pair.ingress.name))
                    continue
                if not server_egress:
                    logging.warn("Neutron SFC: egress port %s not connected." % str(port_pair.egress.name))
                    continue

                compute.dc.net.setChain(
                    server_ingress.name, server_egress.name,
                    port_pair.ingress.intf_name, port_pair.egress.intf_name,
                    cmd="add-flow", cookie=self.cookie, priority=10, bidirectional=False,
                    monitor=False
                )

    def uninstall(self, compute):
        # TODO: implement
        logging.warn("Removing flows is currently not implemented.")

    def update(self):
        # TODO: implement
        logging.warn("Updating flows is currently not implemented.")
