from flask_restful import Resource
from flask import Response, request
from emuvim.api.openstack.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
import emuvim.api.openstack.docker_util as DockerUtil
import logging
import json
import time


class MonitorDummyApi(BaseOpenstackDummy):
    def __init__(self, inc_ip, inc_port):
        super(MonitorDummyApi, self).__init__(inc_ip, inc_port)

        self.api.add_resource(MonitorVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnf, "/v1/monitor/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnfAbs, "/v1/monitor/abs/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(MonitorVnfDcStack, "/v1/monitor/<dc>/<stack>/<vnf_name>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(Shutdown, "/shutdown")

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % ("MonitorDummyApi", self.ip, self.port))
        if self.app is not None:
            self.app.run(self.ip, self.port, debug=True, use_reloader=False, threaded=True)


class Shutdown(Resource):
    """
    A get request to /shutdown will shut down this endpoint.
    """

    def get(self):
        logging.debug(("%s is beeing shut down") % (__name__))
        func = request.environ.get('werkzeug.server.shutdown')
        if func is None:
            raise RuntimeError('Not running with the Werkzeug Server')
        func()


class MonitorVersionsList(Resource):
    def __init__(self, api):
        self.api = api


    def get(self):
        """
        List API versions.

        :return: Returns the api versions.
        :rtype: :class:`flask.response`
        """
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        # at least let it look like an open stack function
        try:
            resp = dict()
            resp['versions'] = dict()
            resp['versions'] = [{
                "id": "v1",
                "links": [{
                    "href": "http://%s:%d/v1/" % (self.api.ip, self.api.port),
                    "rel": "self"
                }],
                "status": "CURRENT",
                "version": "1",
                "min_version": "1",
                "updated": "2013-07-23T11:33:21Z"
            }]

            return Response(json.dumps(resp), status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class MonitorVnf(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, vnf_name):
        """
        Calculates the workload for the specified docker container. Requires at least one second, to calculate
        the network traffic and cpu usage over time.

        :param vnf_name: Specifies the docker container via name.
        :type vnf_name: ``str``
        :return: Returns a json response with network, cpu and memory usage over time, and specifies the storage
            access, the number of running processes and the current system time.
        :rtype: :class:`flask.response`
        """
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        if len(vnf_name) < 3 or 'mn.' != vnf_name[:3]:
            vnf_name = 'mn.' + vnf_name

        found = False
        from emuvim.api.heat.openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            if vnf_name[3:] in api.compute.dc.net:
                found = True
                break

        if not found:
            return Response(u"MonitorAPI: VNF %s does not exist.\n" % (vnf_name[3:]),
                            status=500,
                            mimetype="application/json")
        try:
            docker_id = DockerUtil.docker_container_id(vnf_name)
            out_dict = dict()
            out_dict.update(DockerUtil.monitoring_over_time(docker_id))
            out_dict.update(DockerUtil.docker_mem(docker_id))
            out_dict.update(DockerUtil.docker_PIDS(docker_id))
            out_dict['SYS_time'] = int(time.time() * 1000000000)

            response = Response(json.dumps(out_dict) + '\n', status=200, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as e:
            logging.exception(u"%s: Error getting monitoring information.\n %s" % (__name__, e))
            return Response(u"Error getting monitoring information.\n", status=500, mimetype="application/json")


class MonitorVnfAbs(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, vnf_name):
        """
        Calculates the workload for the specified docker container, at this point in time.

        :param vnf_name: Specifies the docker container via name.
        :type vnf_name: ``str``
        :return: Returns a json response with network, cpu, memory usage and storage access, as absolute values from
            startup till this point of time. It also contains the number of running processes and the current
            system time.
        :rtype: :class:`flask.response`
        """
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))
        if len(vnf_name) < 3 or 'mn.' != vnf_name[:3]:
            vnf_name = 'mn.' + vnf_name

        found = False
        from emuvim.api.heat.openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            if vnf_name[3:] in api.compute.dc.net:
                found = True
                break
        if not found:
            return Response(u"MonitorAPI: VNF %s does not exist\n" % vnf_name[3:],
                            status=500,
                            mimetype="application/json")
        try:
            docker_id = DockerUtil.docker_container_id(vnf_name)
            out_dict = dict()
            out_dict.update(DockerUtil.docker_abs_cpu(docker_id))
            out_dict.update(DockerUtil.docker_mem(docker_id))
            out_dict.update(DockerUtil.docker_abs_net_io(docker_id))
            out_dict.update(DockerUtil.docker_block_rw(docker_id))
            out_dict.update(DockerUtil.docker_PIDS(docker_id))
            out_dict['SYS_time'] = int(time.time() * 1000000000)

            response = Response(json.dumps(out_dict) + '\n', status=200, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as e:
            logging.exception(u"%s: Error getting monitoring information.\n %s" % (__name__, e))
            return Response(u"Error getting monitoring information.\n", status=500, mimetype="application/json")


class MonitorVnfDcStack(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, dc, stack, vnf_name):
        """
        Calculates the workload for the specified docker container, at this point in time.
        This api call is for the translator to monitor a vnfs of a specific datacenter and stack.

        :param dc: Target datacenter.
        :type dc: ``str``
        :param stack: Target stack
        :type stack: ``str``
        :param vnf_name: Specifies the docker container via name.
        :type vnf_name: ``str``
        :return: Returns a json response with network, cpu, memory usage and storage access, as absolute values from
            startup till this point of time. It also contains the number of running processes and the current
            system time.
        :rtype: :class:`flask.response`
        """
        logging.debug("API CALL: %s GET" % str(self.__class__.__name__))

        # search for real name
        vnf_name = self._findName(dc, stack, vnf_name)

        if type(vnf_name) is not str:
            # something went wrong, vnf_name is a Response object
            return vnf_name

        try:
            docker_id = DockerUtil.docker_container_id(vnf_name)
            out_dict = dict()
            out_dict.update(DockerUtil.monitoring_over_time(docker_id))
            out_dict.update(DockerUtil.docker_mem(docker_id))
            out_dict.update(DockerUtil.docker_PIDS(docker_id))
            out_dict['SYS_time'] = int(time.time() * 1000000000)

            response = Response(json.dumps(out_dict) + '\n', status=200, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response
        except Exception as e:
            logging.exception(u"%s: Error getting monitoring information.\n %s" % (__name__, e))
            return Response(u"Error getting monitoring information.\n", status=500, mimetype="application/json")

    # Tries to find real container name according to heat template names
    # Returns a string or a Response object
    def _findName(self, dc, stack, vnf):
        dc_real = None
        from emuvim.api.heat.openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            # search for datacenters
            if dc in api.manage.net.dcs:
                dc_real = api.manage.net.dcs[dc]
                break
        if dc_real is None:
            return Response(u"DC %s does not exist\n" % (dc), status=500, mimetype="application/json")

        # search for related OpenStackAPIs
        api_real = None
        for api in OpenstackApiEndpoint.dc_apis:
            if api.compute.dc == dc_real:
                api_real = api
        if api_real is None:
            return Response(u"OpenStackAPI does not exist\n", status=500, mimetype="application/json")
        # search for stacks
        stack_real = None
        for stackObj in api_real.compute.stacks.values():
            if stackObj.stack_name == stack:
                stack_real = stackObj
        if stack_real is None:
            return Response(u"Stack %s does not exist\n" % (stack), status=500, mimetype="application/json")
        # search for servers
        server_real = None
        for server in stack_real.servers.values():
            if server.template_name == vnf:
                server_real = server
                break
        if server_real is None:
            return Response(u"VNF %s does not exist\n" % (vnf), status=500, mimetype="application/json")
        container_real = 'mn.' + server_real.name
        return container_real
