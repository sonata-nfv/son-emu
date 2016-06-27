import logging
import threading
from flask import Flask, request
from flask_restful import Resource,Api
import json



logging.basicConfig(level=logging.INFO)


dcs = {}

class RestApiEndpoint(object):

    """
    Simple API endpoint that offers a REST
    interface. This interface will be used by the
    default command line client.
    """
    global dcs

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

        # setup endpoints
        self.api.add_resource(ComputeList, "/restapi/compute/<dc_label>")
        self.api.add_resource(ComputeStart, "/restapi/compute/<dc_label>/<compute_name>/start")
        self.api.add_resource(ComputeStop, "/restapi/compute/<dc_label>/<compute_name>/stop")
        self.api.add_resource(ComputeStatus, "/restapi/compute/<dc_label>/<compute_name>")
        self.api.add_resource(DatacenterList, "/restapi/datacenter")
        self.api.add_resource(DatacenterStatus, "/restapi/datacenter/<dc_label>")

        logging.debug("Created API endpoint %s(%s:%d)" % (self.__class__.__name__, self.ip, self.port))


    def connectDatacenter(self, dc):
        dcs[dc.label] = dc
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))

    def start(self):
        thread = threading.Thread(target= self._start_flask, args=())
        thread.daemon = True
        thread.start()
        logging.info("Started API endpoint @ http://%s:%d" % (self.ip, self.port))


    def _start_flask(self):
        self.app.run(self.ip, self.port, debug=True, use_reloader=False)


class ComputeStart(Resource):
    """
    Start a new compute instance: A docker container (note: zerorpc does not support keyword arguments)
    :param dc_label: name of the DC
    :param compute_name: compute container name
    :param image: image name
    :param command: command to execute
    :param network: list of all interface of the vnf, with their parameters (id=id1,ip=x.x.x.x/x),...
    :return: networks list({"id":"input","ip": "10.0.0.254/8"}, {"id":"output","ip": "11.0.0.254/24"})
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
            return  c. getStatus(), 200
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
