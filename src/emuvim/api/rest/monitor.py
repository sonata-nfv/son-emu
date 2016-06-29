import logging
from flask_restful import Resource
from flask import request
import json

logging.basicConfig(level=logging.INFO)

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

    def put(self, vnf_name, vnf_interface, metric):
        logging.debug("REST CALL: start monitor VNF interface")
        try:
            c = net.monitor_agent.setup_metric(vnf_name, vnf_interface, metric)
            # return monitor message response
            return  str(c), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500

    def delete(self, vnf_name, vnf_interface, metric):
        logging.debug("REST CALL: stop monitor VNF interface")
        try:
            c = net.monitor_agent.stop_metric(vnf_name, vnf_interface, metric)
            # return monitor message response
            return str(c), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500


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

    def put(self, vnf_name, vnf_interface, metric, cookie):
        logging.debug("REST CALL: start monitor VNF interface")
        try:
            c = net.monitor_agent.setup_flow(vnf_name, vnf_interface, metric, cookie)
            # return monitor message response
            return str(c), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500

    def delete(self, vnf_name, vnf_interface, metric, cookie):
        logging.debug("REST CALL: stop monitor VNF interface")
        try:
            c = net.monitor_agent.stop_flow(vnf_name, vnf_interface, metric, cookie)
            # return monitor message response
            return str(c), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500