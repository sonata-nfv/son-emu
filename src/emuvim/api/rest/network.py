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

"""
Distributed Cloud Emulator (dcemulator)
Networking and monitoring functions
(c) 2015 by Steven Van Rossem <steven.vanrossem@intec.ugent.be>
"""

import logging
from flask_restful import Resource
from flask import request
import json

logging.basicConfig(level=logging.INFO)

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

# the global net is set from the topology file, and connected via connectDCNetwork function in rest_api_endpoint.py
net = None


class NetworkAction(Resource):
    """
    Add or remove chains between VNFs. These chain links are implemented as flow entries in the networks' SDN switches.
    :param vnf_src_name: VNF name of the source of the link
    :param vnf_dst_name: VNF name of the destination of the link
    :param vnf_src_interface: VNF interface name of the source of the link
    :param vnf_dst_interface: VNF interface name of the destination of the link
    :param weight: weight of the link (can be useful for routing calculations)
    :param match: OpenFlow match format of the flow entry
    :param bidirectional: boolean value if the link needs to be implemented from src to dst and back
    :param cookie: cookie value, identifier of the flow entry to be installed.
    :param priority: integer indicating the priority of the flow entry
    :param skip_vlan_tag: boolean to indicate whether a new vlan tag should be created for this chain
    :param monitor: boolean to indicate whether a new vlan tag should be created for this chain
    :param monitor_placement: 'tx'=place the monitoring flowrule at the beginning of the chain, 'rx'=place at the end of the chain
    :return: message string indicating if the chain action is succesful or not
    """

    global net

    def put(self, vnf_src_name, vnf_dst_name):
        logging.debug("REST CALL: network chain add")
        command = 'add-flow'
        return self._NetworkAction(vnf_src_name, vnf_dst_name, command=command)

    def delete(self, vnf_src_name, vnf_dst_name):
        logging.debug("REST CALL: network chain remove")
        command = 'del-flows'
        return self._NetworkAction(vnf_src_name, vnf_dst_name, command=command)

    def _NetworkAction(self, vnf_src_name, vnf_dst_name, command=None):
        # call DCNetwork method, not really datacenter specific API for now...
        # no check if vnfs are really connected to this datacenter...
        try:
            # check if json data is a dict
            data = request.json
            if data is None:
                data = {}
            elif type(data) is not dict:
                data = json.loads(request.json)

            vnf_src_interface = data.get("vnf_src_interface")
            vnf_dst_interface = data.get("vnf_dst_interface")
            weight = data.get("weight")
            match = data.get("match")
            bidirectional = data.get("bidirectional")
            cookie = data.get("cookie")
            priority = data.get("priority")
            skip_vlan_tag = data.get("skip_vlan_tag")
            monitor = data.get("monitor")
            monitor_placement = data.get("monitor_placement")

            c = net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=vnf_src_interface,
                vnf_dst_interface=vnf_dst_interface,
                cmd=command,
                weight=weight,
                match=match,
                bidirectional=bidirectional,
                cookie=cookie,
                priority=priority,
                skip_vlan_tag=skip_vlan_tag,
                monitor=monitor,
                monitor_placement=monitor_placement)
            # return setChain response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER
