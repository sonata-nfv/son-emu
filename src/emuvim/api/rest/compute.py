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
import logging
from flask_restful import Resource
from flask import request
import json
import threading

logging.basicConfig()

CORS_HEADER = {'Access-Control-Allow-Origin': '*'}

# the dcs dict is set in the rest_api_endpoint.py upon datacenter init
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

        # deploy new container
        # check if json data is a dict
        data = request.json
        if data is None:
            data = {}
        elif not isinstance(data, dict):
            data = json.loads(request.json)

        network = data.get("network")
        nw_list = self._parse_network(network)
        image = data.get("image")
        command = data.get("docker_command")

        try:
            if compute_name is None or compute_name == "None":
                logging.error("No compute name defined in request.")
                return "No compute name defined in request.", 500, CORS_HEADER
            if dc_label is None or dcs.get(dc_label) is None:
                logging.error("No datacenter defined in request.")
                return "No datacenter defined in request.", 500, CORS_HEADER
            c = dcs.get(dc_label).startCompute(
                compute_name, image=image, command=command, network=nw_list)
            # (if available) trigger emu. entry point given in Dockerfile
            try:
                config = c.dcinfo.get("Config", dict())
                env = config.get("Env", list())
                legacy_command_execution = False
                for env_var in env:
                    var, cmd = map(str.strip, map(str, env_var.split('=', 1)))
                    logging.debug("%r = %r" % (var, cmd))
                    if var == "SON_EMU_CMD" or var == "VIM_EMU_CMD":
                        logging.info("Executing script in '{}': {}={}"
                                     .format(compute_name, var, cmd))
                        # execute command in new thread to ensure that API is
                        # not blocked by VNF
                        t = threading.Thread(target=c.cmdPrint, args=(cmd,))
                        t.daemon = True
                        t.start()
                        legacy_command_execution = True
                        break
                if not legacy_command_execution:
                    c.start()
            except Exception as ex:
                logging.warning("Couldn't run Docker entry point VIM_EMU_CMD")
                logging.exception(
                    "Exception: " + str(ex) + "; " + str(type(ex))
                )
            # return docker inspect dict
            return c.getStatus(), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def get(self, dc_label, compute_name):

        logging.debug("API CALL: compute status")

        try:
            return dcs.get(dc_label).containers.get(
                compute_name).getStatus(), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def delete(self, dc_label, compute_name):
        logging.debug("API CALL: compute stop")
        try:
            return dcs.get(dc_label).stopCompute(
                compute_name), 200, CORS_HEADER
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
                for dc in dcs.values():
                    all_containers += dc.listCompute()
                container_list = [(c.name, c.getStatus())
                                  for c in all_containers]
                return container_list, 200, CORS_HEADER
            else:
                # return list of compute nodes for specified DC
                container_list = [(c.name, c.getStatus())
                                  for c in dcs.get(dc_label).listCompute()]
                return container_list, 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER


class ComputeResources(Resource):
    """
    Update the container's resources using the docker.update function
    re-using the same parameters:
        url params:
           blkio_weight
           cpu_period, cpu_quota, cpu_shares
           cpuset_cpus
           cpuset_mems
           mem_limit
           mem_reservation
           memswap_limit
           kernel_memory
           restart_policy
    see https://docs.docker.com/engine/reference/commandline/update/
    or API docs: https://docker-py.readthedocs.io/en/stable/api.html#module-docker.api.container
    :param dc_label: name of the DC
    :param compute_name: compute container name

    :return: docker inspect dict of deployed docker
    """
    global dcs

    def put(self, dc_label, compute_name):
        logging.debug("REST CALL: update container resources")

        try:
            c = self._update_resources(dc_label, compute_name)
            return c.getStatus(), 200, CORS_HEADER
        except Exception as ex:
            logging.exception("API error.")
            return ex.message, 500, CORS_HEADER

    def _update_resources(self, dc_label, compute_name):

        # get URL parameters
        params = request.args
        # then no data
        if params is None:
            params = {}
        logging.debug(
            "REST CALL: update container resources {0}".format(params))
        # check if container exists
        d = dcs.get(dc_label).net.getNodeByName(compute_name)

        # general request of cpu percentage
        # create a mutable copy
        params = params.to_dict()
        if 'cpu_bw' in params:
            cpu_period = int(dcs.get(dc_label).net.cpu_period)
            value = params.get('cpu_bw')
            cpu_quota = int(cpu_period * float(value))
            # put default values back
            if float(value) <= 0:
                cpu_period = 100000
                cpu_quota = -1
            params['cpu_period'] = cpu_period
            params['cpu_quota'] = cpu_quota
            # d.updateCpuLimit(cpu_period=cpu_period, cpu_quota=cpu_quota)

        # only pass allowed keys to docker
        allowed_keys = ['blkio_weight', 'cpu_period', 'cpu_quota', 'cpu_shares', 'cpuset_cpus',
                        'cpuset_mems', 'mem_limit', 'mem_reservation', 'memswap_limit',
                        'kernel_memory', 'restart_policy']
        filtered_params = {key: params[key]
                           for key in allowed_keys if key in params}

        d.update_resources(**filtered_params)

        return d


class DatacenterList(Resource):
    global dcs

    def get(self):
        logging.debug("API CALL: datacenter list")
        try:
            return [d.getStatus() for d in dcs.values()], 200, CORS_HEADER
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
