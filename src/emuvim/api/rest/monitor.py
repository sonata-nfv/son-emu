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

    def put(self, vnf_name, vnf_interface=None, metric='tx_packets'):
        logging.debug("REST CALL: start monitor VNF interface")
        try:
            c = net.monitor_agent.setup_metric(vnf_name, vnf_interface, metric)
            # return monitor message response
            return  str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self, vnf_name, vnf_interface=None, metric='tx_packets'):
        logging.debug("REST CALL: stop monitor VNF interface")
        try:
            c = net.monitor_agent.stop_metric(vnf_name, vnf_interface, metric)
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

    def put(self, vnf_name, vnf_interface=None, metric='tx_packets', cookie=0):
        logging.debug("REST CALL: start monitor VNF interface")
        try:
            c = net.monitor_agent.setup_flow(vnf_name, vnf_interface, metric, cookie)
            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self, vnf_name, vnf_interface=None, metric='tx_packets', cookie=0):
        logging.debug("REST CALL: stop monitor VNF interface")
        try:
            c = net.monitor_agent.stop_flow(vnf_name, vnf_interface, metric, cookie)
            # return monitor message response
            return str(c), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER
