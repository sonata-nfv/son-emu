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


class PortPair(object):
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.tenant_id = "abcdefghijklmnopqrstuvwxyz123456"
        self.name = name
        self.description = ""
        self.ingress = None
        self.egress = None
        self.service_function_parameters = dict()

    def create_dict(self, compute):
        representation = {
            "name": self.name,
            "tenant_id": self.tenant_id,
            "description": self.description,
            "ingress": self.ingress.id,
            "egress": self.egress.id,
            "id": self.id
        }
        return representation
