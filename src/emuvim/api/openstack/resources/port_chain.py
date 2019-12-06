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

        # Cookie for internal identification of installed flows (e.g. to delete
        # them)
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

    def _get_port_pair(self, port_pair_group_id, compute):
        port_pair_group = compute.find_port_pair_group_by_name_or_id(port_pair_group_id)
        if len(port_pair_group.port_pairs) != 1:
            raise RuntimeError("Only port pair groups with a single port pair are supported!")
        return compute.find_port_pair_by_name_or_id(port_pair_group.port_pairs[0])

    def install(self, compute):

        port_pair_chain = map(lambda port_pair_group_id: self._get_port_pair(port_pair_group_id, compute),
                              self.port_pair_groups)
        ingress_ports = list(map(lambda port_pair: port_pair.ingress, port_pair_chain))
        egress_ports = list(map(lambda port_pair: port_pair.ingress, port_pair_chain))
        chain_start = ingress_ports[0]
        chain_rest = ingress_ports[1:]

        for flow_classifier_id in self.flow_classifiers:
            flow_classifier = compute.find_flow_classifier_by_name_or_id(flow_classifier_id)
            if not flow_classifier:
                raise RuntimeError("Unable to find flow_classifier %s" % flow_classifier_id)

            port = compute.find_port_by_name_or_id(flow_classifier.logical_source_port)

            chain = [(port, chain_start)] + list(zip(egress_ports, chain_rest))

            for (egress_port, ingress_port) in chain:
                server_egress = None
                server_ingress = None
                for server in compute.computeUnits.values():
                    if egress_port.name in server.port_names or egress_port.id in server.port_names:
                        server_egress = server
                    if ingress_port.name in server.port_names or ingress_port.id in server.port_names:
                        server_ingress = server

                if not server_egress:
                    raise RuntimeError("Neutron SFC: egress port %s not connected to any server." %
                                       egress_port.name)
                if not server_ingress:
                    raise RuntimeError("Neutron SFC: ingress port %s not connected to any server." %
                                       ingress_port.name)

                compute.dc.net.setChain(
                    server_egress.name, server_ingress.name,
                    egress_port.intf_name, ingress_port.intf_name,
                    match=flow_classifier.to_match(),
                    mod_dl_dst=ingress_port.mac_address,
                    cmd="add-flow", cookie=self.cookie, priority=10, bidirectional=False,
                    monitor=False, skip_vlan_tag=True
                )

    def uninstall(self, compute):
        # TODO: implement
        logging.warn("Removing flows is currently not implemented.")

    def update(self):
        # TODO: implement
        logging.warn("Updating flows is currently not implemented.")
