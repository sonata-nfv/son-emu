import logging
from flask_restful import Resource
from flask import request
import json

logging.basicConfig(level=logging.INFO)

dcs = {}

class ComputeStart(Resource):
    """
    Start a new compute instance: A docker container (note: zerorpc does not support keyword arguments)
    :param dc_label: name of the DC
    :param compute_name: compute container name
    :param image: image name
    :param command: command to execute
    :param network: list of all interface of the vnf, with their parameters (id=id1,ip=x.x.x.x/x),...
    example networks list({"id":"input","ip": "10.0.0.254/8"}, {"id":"output","ip": "11.0.0.254/24"})
    :return: docker inspect dict of deployed docker
    """
    global dcs

    def put(self, dc_label, compute_name):
        logging.debug("API CALL: compute start")
        try:

            image = json.loads(request.json).get("image")
            network = json.loads(request.json).get("network")
            command = json.loads(request.json).get("docker_command")
            c = dcs.get(dc_label).startCompute(
                compute_name, image= image, command= command, network= network)
            # return docker inspect dict
            return c.getStatus(), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500

class ComputeStop(Resource):

    global dcs

    def get(self, dc_label, compute_name):
        logging.debug("API CALL: compute stop")
        try:
            return dcs.get(dc_label).stopCompute(compute_name), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message,500


class ComputeList(Resource):

    global dcs

    def get(self, dc_label):
        logging.debug("API CALL: compute list")
        try:
            if dc_label == 'None':
                # return list with all compute nodes in all DCs
                all_containers = []
                for dc in dcs.itervalues():
                    all_containers += dc.listCompute()
                return [(c.name, c.getStatus()) for c in all_containers], 200
            else:
                # return list of compute nodes for specified DC
                return [(c.name, c.getStatus())
                    for c in dcs.get(dc_label).listCompute()], 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500


class ComputeStatus(Resource):

    global dcs

    def get(self, dc_label, compute_name):

        logging.debug("API CALL: compute list")

        try:
            return dcs.get(dc_label).containers.get(compute_name).getStatus(), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500

class DatacenterList(Resource):

    global dcs

    def get(self):
        logging.debug("API CALL: datacenter list")
        try:
            return [d.getStatus() for d in dcs.itervalues()], 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500

class DatacenterStatus(Resource):

    global dcs

    def get(self, dc_label):
        logging.debug("API CALL: datacenter status")
        try:
            return dcs.get(dc_label).getStatus(), 200
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500
