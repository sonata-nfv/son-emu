"""
Copyright (c) 2017 SONATA-NFV and Paderborn University
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

Neither the name of the SONATA-NFV, Paderborn University
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
import uuid


class FlowClassifier(object):
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.tenant_id = "abcdefghijklmnopqrstuvwxyz123456"
        self.name = name
        self.description = ""
        self.ethertype = "IPv4"
        self.protocol = None
        self.source_port_range_min = 0
        self.source_port_range_max = 0
        self.destination_port_range_min = 0
        self.destination_port_range_max = 0
        self.source_ip_prefix = None
        self.destination_ip_prefix = None
        self.logical_source_port = ""
        self.logical_destination_port = ""
        self.l7_parameters = dict()

    def create_dict(self, compute):
        representation = {
            "name": self.name,
            "tenant_id": self.tenant_id,
            "description": self.description,
            "id": self.id,
        }
        if self.ethertype:
            representation["ethertype"] = self.ethertype
        if self.protocol:
            representation["protocol"] = self.protocol
        if self.source_port_range_min:
            representation["source_port_range_min"] = self.source_port_range_min
        if self.source_port_range_max:
            representation["source_port_range_max"] = self.source_port_range_max
        if self.destination_port_range_min:
            representation["destination_port_range_min"] = self.destination_port_range_min
        if self.destination_port_range_max:
            representation["destination_port_range_max"] = self.destination_port_range_max
        if self.source_ip_prefix:
            representation["source_ip_prefix"] = self.source_ip_prefix
        if self.destination_ip_prefix:
            representation["destination_ip_prefix"] = self.destination_ip_prefix
        if len(self.logical_source_port):
            representation["logical_source_port"] = self.logical_source_port
        if len(self.logical_destination_port):
            representation["logical_destination_port"] = self.logical_destination_port
        if len(self.l7_parameters.items()):
            representation["l7_parameters"] = self.l7_parameters

        return representation
