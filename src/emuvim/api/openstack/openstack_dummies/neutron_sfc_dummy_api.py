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
from flask_restful import Resource
from flask import request, Response
import logging
import json
import uuid

from emuvim.api.openstack.resources.port_chain import PortChain
from emuvim.api.openstack.helper import get_host


class SFC(Resource):
    def __init__(self, api):
        self.api = api


###############################################################################
# Port Pair
###############################################################################

class PortPairsCreate(SFC):
    def post(self):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("port_pair")
            name = request_dict["name"]

            ingress_port = self.api.compute.find_port_by_name_or_id(request_dict["ingress"])
            egress_port = self.api.compute.find_port_by_name_or_id(request_dict["egress"])

            port_pair = self.api.compute.create_port_pair(name)
            port_pair.ingress = ingress_port
            port_pair.egress = egress_port
            if "description" in request_dict:
                port_pair.description = request_dict["description"]
            if "service_function_parameters" in request_dict:
                port_pair.service_function_parameters = request_dict["service_function_parameters"]

            resp = {
                "port_pair": port_pair.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=201, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairsUpdate(SFC):
    def put(self, pair_id):
        logging.debug("API CALL: %s PUT" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("port_pair")
            port_pair = self.api.compute.find_port_pair_by_name_or_id(pair_id)
            if "name" in request_dict:
                port_pair.name = request_dict["name"]
            if "description" in request_dict:
                port_pair.description = request_dict["description"]

            resp = {
                "port_pair": port_pair.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairsDelete(SFC):
    def delete(self, pair_id):
        logging.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            self.api.compute.delete_port_pair(pair_id)

            return Response("Port pair %s deleted.\n" % pair_id, status=204, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairsList(SFC):
    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            port_pair_list = []
            for port_pair in self.api.compute.port_pairs.values():
                port_pair_list.append(port_pair.create_dict(self.api.compute))
            resp = {"port_pairs": port_pair_list}

            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairsShow(SFC):
    def get(self, pair_id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            port_pair = self.api.compute.find_port_pair_by_name_or_id(pair_id)
            resp = {
                "port_pair": port_pair.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


###############################################################################
# Port Pair Group
###############################################################################

class PortPairGroupCreate(SFC):
    def post(self):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("port_pair_group")

            port_pair_group = self.api.compute.create_port_pair_group(request_dict["name"])
            port_pair_group.port_pairs = request_dict["port_pairs"]
            if "description" in request_dict:
                port_pair_group.description = request_dict["description"]
            if "port_pair_group_parameters" in request_dict:
                port_pair_group.port_pair_group_parameters = request_dict["port_pair_group_parameters"]

            resp = {
                "port_pair_group": port_pair_group.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=201, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairGroupUpdate(SFC):
    def put(self, group_id):
        logging.debug("API CALL: %s PUT" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("port_pair_group")
            port_pair_group = self.api.compute.find_port_pair_group_by_name_or_id(group_id)
            if "name" in request_dict:
                port_pair_group.name = request_dict["name"]
            if "description" in request_dict:
                port_pair_group.description = request_dict["description"]
            if "port_pairs" in request_dict:
                port_pair_group.port_pairs = request_dict["port_pairs"]

            resp = {
                "port_pair_group": port_pair_group.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairGroupDelete(SFC):
    def delete(self, group_id):
        logging.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            self.api.compute.delete_port_pair_group(group_id)

            return Response("Port pair group %s deleted.\n" % group_id, status=204, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairGroupList(SFC):
    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            port_pair_group_list = []
            for port_pair_group in self.api.compute.port_pair_groups.values():
                port_pair_group_list.append(port_pair_group.create_dict(self.api.compute))
            resp = {"port_pair_groups": port_pair_group_list}

            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortPairGroupShow(SFC):
    def get(self, group_id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            port_pair_group = self.api.compute.find_port_pair_group_by_name_or_id(group_id)
            resp = {
                "port_pair_group": port_pair_group.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


###############################################################################
# Flow Classifier
###############################################################################

class FlowClassifierCreate(SFC):
    def post(self):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("flow_classifier")

            flow_classifier = self.api.compute.create_flow_classifier(request_dict["name"])
            if "description" in request_dict:
                flow_classifier.description = request_dict["description"]
            if "ethertype" in request_dict:
                flow_classifier.ethertype = request_dict["ethertype"]
            if "protocol" in request_dict:
                flow_classifier.protocol = request_dict["protocol"]
            if "source_port_range_min" in request_dict:
                flow_classifier.source_port_range_min = request_dict["source_port_range_min"]
            if "source_port_range_max" in request_dict:
                flow_classifier.source_port_range_max = request_dict["source_port_range_max"]
            if "destination_port_range_min" in request_dict:
                flow_classifier.destination_port_range_min = request_dict["destination_port_range_min"]
            if "destination_port_range_max" in request_dict:
                flow_classifier.destination_port_range_max = request_dict["destination_port_range_max"]
            if "source_ip_prefix" in request_dict:
                flow_classifier.source_ip_prefix = request_dict["source_ip_prefix"]
            if "destination_ip_prefix" in request_dict:
                flow_classifier.destination_ip_prefix = request_dict["destination_ip_prefix"]
            if "logical_source_port" in request_dict:
                flow_classifier.logical_source_port = request_dict["logical_source_port"]
            if "logical_destination_port" in request_dict:
                flow_classifier.logical_destination_port = request_dict["logical_destination_port"]
            if "l7_parameters" in request_dict:
                flow_classifier.l7_parameters = request_dict["l7_parameters"]

            resp = {
                "flow_classifier": flow_classifier.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=201, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class FlowClassifierUpdate(SFC):
    def put(self, flow_classifier_id):
        logging.debug("API CALL: %s PUT" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("flow_classifier")
            flow_classifier = self.api.compute.find_flow_classifier_by_name_or_id(flow_classifier_id)
            if "name" in request_dict:
                flow_classifier.name = request_dict["name"]
            if "description" in request_dict:
                flow_classifier.description = request_dict["description"]

            resp = {
                "flow_classifier": flow_classifier.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class FlowClassifierDelete(SFC):
    def delete(self, flow_classifier_id):
        logging.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            self.api.compute.delete_flow_classifier(flow_classifier_id)

            return Response("Port pair group %s deleted.\n" % flow_classifier_id, status=204,
                            mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class FlowClassifierList(SFC):
    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            flow_classifier_list = []
            for flow_classifier in self.api.compute.flow_classifiers.values():
                flow_classifier_list.append(flow_classifier.create_dict(self.api.compute))
            resp = {"flow_classifiers": flow_classifier_list}

            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class FlowClassifierShow(SFC):
    def get(self, flow_classifier_id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            flow_classifier = self.api.compute.find_flow_classifier_by_name_or_id(flow_classifier_id)
            resp = {
                "flow_classifier": flow_classifier.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


###############################################################################
# Port Chain
###############################################################################

class PortChainCreate(SFC):
    def post(self):
        logging.debug("API CALL: %s POST" % str(self.__class__.__name__))

        try:
            request_dict = json.loads(request.data).get("port_chain")

            port_chain = self.api.compute.create_port_chain(request_dict["name"])
            port_chain.port_pair_groups = request_dict["port_pair_groups"]
            if "description" in request_dict:
                port_chain.description = request_dict["description"]
            if "flow_classifiers" in request_dict:
                port_chain.flow_classifiers = request_dict["flow_classifiers"]
            if "chain_parameters" in request_dict:
                port_chain.chain_parameters = request_dict["chain_parameters"]

            port_chain.install(self.api.compute)

            resp = {
                "port_chain": port_chain.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=201, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortChainUpdate(SFC):
    def put(self, chain_id):
        logging.debug("API CALL: %s PUT" % str(self.__class__.__name__))
        request_dict = json.loads(request.data).get("port_chain")

        port_chain = self.api.compute.find_port_chain_by_name_or_id(chain_id)
        if "name" in request_dict:
            port_chain.name = request_dict["name"]
        if "description" in request_dict:
            port_chain.description = request_dict["description"]
        if "flow_classfiers" in request_dict:
            # TODO: update chain implementation
            port_chain.description = request_dict["flow_classifiers"]
        if "no_flow_classfiers" in request_dict:
            port_chain.description = []
        if "port_pair_groups" in request_dict:
            # TODO: update chain implementation
            port_chain.port_pair_groups = request_dict["port_pair_groups"]

        port_chain.update()
        try:
            resp = {
                "port_chain": port_chain.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortChainDelete(SFC):
    def delete(self, chain_id):
        logging.debug("API CALL: %s DELETE" % str(self.__class__.__name__))

        self.api.compute.delete_port_chain(chain_id)
        try:
            return Response("Port chain %s deleted.\n" % chain_id, status=204, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortChainList(SFC):
    def get(self):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            port_chain_list = []
            for port_chain in self.api.compute.port_chains.values():
                port_chain_list.append(port_chain.create_dict(self.api.compute))
            resp = {"port_chains": port_chain_list}

            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')


class PortChainShow(SFC):
    def get(self, chain_id):
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            port_chain = self.api.compute.find_port_chain_by_name_or_id(chain_id)
            resp = {
                "port_chain": port_chain.create_dict(self.api.compute)
            }
            return Response(json.dumps(resp), status=200, mimetype='application/json')
        except Exception as ex:
            logging.exception("Neutron SFC: %s Exception." % str(self.__class__.__name__))
            return Response(ex.message, status=500, mimetype='application/json')
