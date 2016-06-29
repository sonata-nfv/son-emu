import logging
from flask_restful import Resource
from flask import request
import json

logging.basicConfig(level=logging.INFO)

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
            vnf_src_interface = json.loads(request.json).get("vnf_src_interface")
            vnf_dst_interface = json.loads(request.json).get("vnf_dst_interface")
            weight = json.loads(request.json).get("weight")
            match = json.loads(request.json).get("match")
            bidirectional = json.loads(request.json).get("bidirectional")
            cookie = json.loads(request.json).get("cookie")
            c = net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=vnf_src_interface,
                vnf_dst_interface=vnf_dst_interface,
                cmd=command,
                weight=weight,
                match=match,
                bidirectional=bidirectional,
                cookie=cookie)
            # return setChain response
            return str(c), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500