# Copyright (c) 2018 SONATA-NFV and Paderborn University
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
import unittest

from emuvim.api.openstack.resources.flow_classifier import FlowClassifier


class FlowClassifierTest(unittest.TestCase):
    def test_empty_flow_classifier_to_match_conversion(self):
        c = FlowClassifier("test")
        self.assertEqual("dl_type=2048", c.to_match())

    def test_tcp_ip_flow_classifier_to_match_conversion(self):
        c = FlowClassifier("test")
        c.protocol = "tcp"
        c.source_ip_prefix = "10.0.0.10/32"
        c.destination_ip_prefix = "10.0.0.12/32"
        c.destination_port_range_min = 80
        c.destination_port_range_max = 80
        self.assertEqual("dl_type=2048,nw_proto=6,nw_src=10.0.0.10/32,nw_dst=10.0.0.12/32,tp_dst=80", c.to_match())
