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
import logging
from flask_restful import Resource
from flask import request
import json

logging.basicConfig(level=logging.INFO)

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

dcs = {}


class Compute(Resource):
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

    def put(self, dc_label, compute_name, resource=None, value=None):
        # check if resource update
        if resource and value:
           c = self._update_resource(dc_label, compute_name, resource, value)
           return c.getStatus(), 200

        # deploy new container
        # check if json data is a dict
        data = request.json
        if data is None:
            data = {}
        elif type(data) is not dict:
            data = json.loads(request.json)

        network = data.get("network")
        nw_list = self._parse_network(network)
        image = data.get("image")
        command = data.get("docker_command")

        try:
            logging.debug("API CALL: compute start")
            c = dcs.get(dc_label).startCompute(
                compute_name, image=image, command=command, network=nw_list)
            # return docker inspect dict
            return c.getStatus(), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def _update_resource(self, dc_label, compute_name, resource, value):
        #check if container exists
        d = dcs.get(dc_label).net.getNodeByName(compute_name)
        if resource == 'cpu':
            cpu_period = int(dcs.get(dc_label).net.cpu_period)
            cpu_quota = int(cpu_period * float(value))
            #put default values back
            if float(value) <= 0:
                cpu_period = 100000
                cpu_quota = -1
            d.updateCpuLimit(cpu_period=cpu_period, cpu_quota=cpu_quota)
        return d


    def get(self, dc_label, compute_name):

        logging.debug("API CALL: compute status")

        try:
            return dcs.get(dc_label).containers.get(compute_name).getStatus(), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self, dc_label, compute_name):
        logging.debug("API CALL: compute stop")
        try:
            return dcs.get(dc_label).stopCompute(compute_name), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def _parse_network(self, network_str):
        '''
        parse the options for all network interfaces of the vnf
        :param network_str: (id=x,ip=x.x.x.x/x), ...
        :return: list of dicts [{"id":x,"ip":"x.x.x.x/x"}, ...]
        '''
        nw_list = list()

        # TODO make this more robust with regex check
        if network_str is None:
            return nw_list

        networks = network_str[1:-1].split('),(')
        for nw in networks:
            nw_dict = dict(tuple(e.split('=')) for e in nw.split(','))
            nw_list.append(nw_dict)

        return nw_list


class ComputeList(Resource):
    global dcs

    def get(self, dc_label=None):
        logging.debug("API CALL: compute list")
        try:
            if dc_label is None or dc_label == 'None':
                # return list with all compute nodes in all DCs
                all_containers = []
                for dc in dcs.itervalues():
                    all_containers += dc.listCompute()
                return [(c.name, c.getStatus()) for c in all_containers], 200, CORS_HEADER
            else:
                # return list of compute nodes for specified DC
                return [(c.name, c.getStatus())
                        for c in dcs.get(dc_label).listCompute()], 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class DatacenterList(Resource):
    global dcs

    def get(self):
        logging.debug("API CALL: datacenter list")
        try:
            return [d.getStatus() for d in dcs.itervalues()], 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class DatacenterStatus(Resource):
    global dcs

    def get(self, dc_label):
        logging.debug("API CALL: datacenter status")
        try:
            return dcs.get(dc_label).getStatus(), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER
