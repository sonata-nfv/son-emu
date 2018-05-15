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
#
# Distributed Cloud Emulator (dcemulator)
# Networking and monitoring functions
# (c) 2015 by Steven Van Rossem <steven.vanrossem@intec.ugent.be>
import logging
from flask_restful import Resource
from flask import request

logging.basicConfig()

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

net = None


class MonitorInterfaceAction(Resource):
    """
    Monitor the counters of a VNF interface
    :param vnf_name: name of the VNF to be monitored
    :param vnf_interface: name of the VNF interface to be monitored
    :param metric: tx_bytes, rx_bytes, tx_packets, rx_packets
    :return: message string indicating if the monitor action is succesful or not
    """
    global net

    def put(self):
        logging.debug("REST CALL: start monitor VNF interface")
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_name = data.get("vnf_name")
        vnf_interface = data.get("vnf_interface", None)
        metric = data.get("metric", 'tx_packets')
        cookie = data.get("cookie")

        try:
            if cookie:
                c = net.monitor_agent.setup_flow(
                    vnf_name, vnf_interface, metric, cookie)
            else:
                c = net.monitor_agent.setup_metric(
                    vnf_name, vnf_interface, metric)
            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self):
        logging.debug("REST CALL: stop monitor VNF interface")
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_name = data.get("vnf_name")
        vnf_interface = data.get("vnf_interface", None)
        metric = data.get("metric", 'tx_packets')
        cookie = data.get("cookie")

        try:
            if cookie:
                c = net.monitor_agent.stop_flow(
                    vnf_name, vnf_interface, metric, cookie)
            else:
                c = net.monitor_agent.stop_metric(
                    vnf_name, vnf_interface, metric)
            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class MonitorFlowAction(Resource):
    """
    Monitor the counters of a specific flow
    :param vnf_name: name of the VNF to be monitored
    :param vnf_interface: name of the VNF interface to be monitored
    :param metric: tx_bytes, rx_bytes, tx_packets, rx_packets
    :param cookie: specific identifier of flows to monitor
    :return: message string indicating if the monitor action is succesful or not
    """
    global net

    def put(self):
        logging.debug("REST CALL: start monitor VNF interface")
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_name = data.get("vnf_name")
        vnf_interface = data.get("vnf_interface", None)
        metric = data.get("metric", 'tx_packets')
        cookie = data.get("cookie", 0)

        try:
            c = net.monitor_agent.setup_flow(
                vnf_name, vnf_interface, metric, cookie)
            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self):
        logging.debug("REST CALL: stop monitor VNF interface")
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_name = data.get("vnf_name")
        vnf_interface = data.get("vnf_interface", None)
        metric = data.get("metric", 'tx_packets')
        cookie = data.get("cookie", 0)

        try:
            c = net.monitor_agent.stop_flow(
                vnf_name, vnf_interface, metric, cookie)
            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class MonitorLinkAction(Resource):
    """
    Add or remove flow monitoring on chains between VNFs.
    These chain links are implemented as flow entries in the networks' SDN switches.
    The monitoring is an extra flow entry on top of the existing chain, with a specific match. (preserving the chaining)
    The counters of this new monitoring flow are exported
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
    :param metric: tx_packet_rate, tx_byte_rate, rx_packet_rate, rx_byte_rate
    :return: message string indicating if the chain action is succesful or not
    """

    # the global net is set from the topology file, and connected via
    # connectDCNetwork function in rest_api_endpoint.py
    global net

    def put(self):
        logging.debug("REST CALL: monitor link flow add")

        try:
            command = 'add-flow'
            return self._MonitorLinkAction(command=command)
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self):
        logging.debug("REST CALL: monitor link flow remove")

        try:
            command = 'del-flows'
            return self._MonitorLinkAction(command=command)
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def _MonitorLinkAction(self, command=None):
        # call DCNetwork method, not really datacenter specific API for now...
        # no check if vnfs are really connected to this datacenter...

        try:
            # check json payload
            logging.debug("json: {}".format(request.json))
            logging.debug("args: {}".format(request.args))

            data = request.json
            if data is None:
                data = request.args
            if data is None:
                data = {}

            vnf_src_name = data.get("vnf_src_name")
            vnf_dst_name = data.get("vnf_dst_name")
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

            # first install monitor flow
            c1 = net.setChain(
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

            # then export monitor flow
            metric = data.get("metric")
            if 'rx' in monitor_placement:
                vnf_name = vnf_dst_name
                vnf_interface = vnf_dst_interface
            elif 'tx' in monitor_placement:
                vnf_name = vnf_src_name
                vnf_interface = vnf_src_interface

            c2 = 'command unknown'
            if command == 'add-flow':
                c2 = net.monitor_agent.setup_flow(
                    vnf_name, vnf_interface, metric, cookie)
            elif command == 'del-flows':
                c2 = net.monitor_agent.stop_flow(
                    vnf_name, vnf_interface, metric, cookie)

            # return setChain response
            return (str(c1) + " " + str(c2)), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class MonitorSkewAction(Resource):
    """
    Monitor the counters of a VNF interface
    :param vnf_name: name of the VNF to be monitored
    :param resource: the resource to be monitored (cpu, mem, ...)
    :return: message string indicating if the monitor action is succesful or not
    """
    global net

    def put(self):
        logging.debug("REST CALL: start monitor skewness")
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_name = data.get("vnf_name")
        resource_name = data.get("resource_name", 'cpu')
        try:
            # configure skewmon
            c = net.monitor_agent.update_skewmon(
                vnf_name, resource_name, action='start')

            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self):
        logging.debug("REST CALL: stop monitor skewness")
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_name = data.get("vnf_name")
        resource_name = data.get("resource_name", 'cpu')
        try:
            # configure skewmon
            c = net.monitor_agent.update_skewmon(
                vnf_name, resource_name, action='stop')

            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class MonitorTerminal(Resource):
    """
    start a terminal for the selected VNFs
    :param vnf_list: list of names of the VNFs to start a terminal from (all VNFs if None)
    :return: message string indicating if the monitor action is succesful or not
    """
    global net

    def get(self):
        # get URL parameters
        data = request.args
        if data is None:
            data = {}
        vnf_list = data.get("vnf_list")
        logging.debug("REST CALL: start terminal for: {}".format(vnf_list))
        try:
            # start terminals
            c = net.monitor_agent.term(vnf_list)

            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER
