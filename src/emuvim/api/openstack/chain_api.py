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
import json
import logging
import copy

# from gevent import monkey
from gevent.pywsgi import WSGIServer

from mininet.node import OVSSwitch

from flask import Flask
from flask import Response, request
from flask_restful import Api, Resource

# monkey.patch_all()


class ChainApi(Resource):
    """
    The chain API is a component that is not used in OpenStack.
    It is a custom built REST API that can be used to create network chains and loadbalancers.
    """

    def __init__(self, inc_ip, inc_port, manage):
        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)
        self.ip = inc_ip
        self.port = inc_port
        self.manage = manage
        self.playbook_file = '/tmp/son-emu-requests.log'
        self.api.add_resource(ChainVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainList, "/v1/chain/list",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnfInterfaces, "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(ChainVnfDcStackInterfaces,
                              "/v1/chain/<src_dc>/<src_stack>/<src_vnf>/<src_intfs>/<dst_dc>/<dst_stack>/<dst_vnf>/<dst_intfs>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(BalanceHostList, "/v1/lb/list",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(BalanceHost, "/v1/lb/<vnf_src_name>/<vnf_src_interface>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(BalanceHostDcStack, "/v1/lb/<src_dc>/<src_stack>/<vnf_src_name>/<vnf_src_interface>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(QueryTopology, "/v1/topo",
                              resource_class_kwargs={'api': self})

        @self.app.after_request
        def add_access_control_header(response):
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" %
                     ("ChainDummyApi", self.ip, self.port))
        self.http_server = WSGIServer(
            (self.ip, self.port),
            self.app,
            log=open("/dev/null", "w")  # don't show http logs
        )
        self.http_server.serve_forever(stop_timeout=1)
        logging.info('Stopped %s' % self.__class__.__name__)

    def stop(self):
        if self.http_server:
            logging.info('Stopping %s' % self.__class__.__name__)
            self.http_server.stop(timeout=1)

    def dump_playbook(self):
        with self.manage.lock:
            with open(self.playbook_file, 'a') as logfile:
                if len(request.data) > 0:
                    data = "# CHAIN API\n"
                    data += "curl -X {type} -H \"Content-type: application/json\" -d '{data}' {url}".format(type=request.method,
                                                                                                            data=request.data,
                                                                                                            url=request.url)
                    logfile.write(data + "\n")


class ChainVersionsList(Resource):
    '''
    Entrypoint to find versions of the chain api.
    '''

    def __init__(self, api):
        self.api = api

    def get(self):
        '''
        :return: flask.Response containing the openstack like description of the chain api
        '''
        # at least let it look like an open stack function
        try:
            resp = """
                {
                    "versions": [
                        {
                            "id": "v1",
                            "links": [
                                {
                                    "href": "http://%s:%d/v1/",
                                    "rel": "self"
                                }
                            ],
                            "status": "CURRENT",
                            "version": "1",
                            "min_version": "1",
                            "updated": "2013-07-23T11:33:21Z"
                        }
                    ]
                }
            """ % (self.api.ip, self.api.port)

            return Response(resp, status=200, mimetype="application/json")

        except Exception as ex:
            logging.exception(
                u"%s: Could not show list of versions." % __name__)
            return ex.message, 500


class ChainList(Resource):
    '''
    Will retrieve all chains including their paths.
    '''

    def __init__(self, api):
        self.api = api

    def get(self):
        '''
        :return: flask.Response containing all live chains
        '''
        # at least let it look like an open stack function
        try:
            resp = {"chains": list()}

            for chain in self.api.manage.full_chain_data.values():
                resp["chains"].append(chain)

            return Response(json.dumps(resp), status=200,
                            mimetype="application/json")

        except Exception as ex:
            logging.exception(
                u"%s: Could not list all network chains." % __name__)
            return ex.message, 500


class BalanceHostList(Resource):
    '''
    Will retrieve all loadbalance rules including their paths.
    '''

    def __init__(self, api):
        self.api = api

    def get(self):
        '''
        :return: flask.Response containing all live loadbalancer rules
        '''
        # at least let it look like an open stack function
        try:
            resp = {"loadbalancers": list()}

            for lb in self.api.manage.full_lb_data.values():
                resp["loadbalancers"].append(lb)

            return Response(json.dumps(resp), status=200,
                            mimetype="application/json")

        except Exception as ex:
            logging.exception(
                u"%s: Could not list all live loadbalancers." % __name__)
            return ex.message, 500


class ChainVnfInterfaces(Resource):
    """
    Handles requests targeted at: "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
    Requests are for tearing down or setting up a chain between two vnfs
    """

    def __init__(self, api):
        self.api = api

    def put(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        """
        A put request to "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
        will create a chain between two interfaces at the specified vnfs.

        Note:
           Does not allow a custom path. Uses ``.post``
           Internally just makes a POST request with no POST data!

        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param src_intfs: Name of the source VNF interface to chain on
        :type src_intfs: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param dst_intfs: Name of the destination VNF interface to chain on
        :type dst_intfs: ``str``
        :return: flask.Response 200 if set up correctly else 500 also returns the cookie as dict {'cookie': value}
         501 if one of the VNF / intfs does not exist
        :rtype: :class:`flask.Response`
        """
        return self.post(src_vnf, src_intfs, dst_vnf, dst_intfs)

    def post(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        """
         A post request to "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
         will create a chain between two interfaces at the specified vnfs.
         The POST data contains the path like this.
         { "path": ["dc1.s1", "s1", "dc4.s1"]}
         path specifies the destination vnf and interface and contains a list of switches
         that the path traverses. The path may not contain single hop loops like:
         [s1, s2, s1].
         This is a limitation of Ryu, as Ryu does not allow the `INPUT_PORT` action!

        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param src_intfs: Name of the source VNF interface to chain on
        :type src_intfs: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param dst_intfs: Name of the destination VNF interface to chain on
        :type dst_intfs: ``str``
        :return: flask.Response 200 if set up correctly else 500 also returns the cookie as dict {'cookie': value}
         501 if one of the VNF / intfs does not exist
        :rtype: :class:`flask.Response`

        """

        if request.is_json:
            path = request.json.get('path')
            layer2 = request.json.get('layer2', True)
        else:
            path = None
            layer2 = True

        # check if both VNFs exist
        if not self.api.manage.check_vnf_intf_pair(src_vnf, src_intfs):
            return Response(u"VNF %s or intfs %s does not exist" % (src_vnf, src_intfs), status=501,
                            mimetype="application/json")
        if not self.api.manage.check_vnf_intf_pair(dst_vnf, dst_intfs):
            return Response(u"VNF %s or intfs %s does not exist" % (dst_vnf, dst_intfs), status=501,
                            mimetype="application/json")
        try:
            cookie = self.api.manage.network_action_start(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                          vnf_dst_interface=dst_intfs, bidirectional=True,
                                                          path=path, layer2=layer2)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200,
                            mimetype="application/json")

        except Exception as e:
            logging.exception(
                u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain",
                            status=500, mimetype="application/json")

    def delete(self, src_vnf, src_intfs, dst_vnf, dst_intfs):
        """
        A DELETE request to "/v1/chain/<src_vnf>/<src_intfs>/<dst_vnf>/<dst_intfs>"
        will delete a previously created chain.

        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param src_intfs: Name of the source VNF interface to chain on
        :type src_intfs: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param dst_intfs: Name of the destination VNF interface to chain on
        :type dst_intfs: ``str``
        :return: flask.Response 200 if set up correctly else 500\
         also returns the cookie as dict {'cookie': value}
         501 if one of the VNF / intfs does not exist
        :rtype: :class:`flask.Response`

        """
        # check if both VNFs exist
        # check if both VNFs exist
        if not self.api.manage.check_vnf_intf_pair(src_vnf, src_intfs):
            return Response(u"VNF %s or intfs %s does not exist" % (src_vnf, src_intfs), status=501,
                            mimetype="application/json")
        if not self.api.manage.check_vnf_intf_pair(dst_vnf, dst_intfs):
            return Response(u"VNF %s or intfs %s does not exist" % (dst_vnf, dst_intfs), status=501,
                            mimetype="application/json")
        try:
            cookie = self.api.manage.network_action_stop(src_vnf, dst_vnf, vnf_src_interface=src_intfs,
                                                         vnf_dst_interface=dst_intfs, bidirectional=True)
            return Response(json.dumps(cookie), status=200,
                            mimetype="application/json")
        except Exception as e:
            logging.exception(
                u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain",
                            status=500, mimetype="application/json")


class ChainVnfDcStackInterfaces(Resource):
    '''
    Handles requests targeted at: "/v1/chain/<src_dc>/<src_stack>/<src_vnf>/<src_intfs>/<dst_dc>/<dst_stack>/<dst_vnf>/<dst_intfs>"
    Handles tearing down or setting up a chain between two vnfs for stacks.
    '''

    def __init__(self, api):
        self.api = api

    def put(self, src_dc, src_stack, src_vnf, src_intfs,
            dst_dc, dst_stack, dst_vnf, dst_intfs):
        """
        A PUT request to "/v1/chain/<src_dc>/<src_stack>/<src_vnf>/<src_intfs>/<dst_dc>/<dst_stack>/<dst_vnf>/<dst_intfs>"
        will set up chain.

        :Note: PUT Requests can not set up custom paths!

        :param src_dc: Name of the source datacenter
        :type src_dc: `str`
        :param src_stack: Name of the source stack
        :type src_stack: `str`
        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param src_intfs: Name of the source VNF interface to chain on
        :type src_intfs: ``str``
        :param dst_dc: Name of the destination datacenter
        :type dst_dc: ``str``
        :param dst_stack: Name of the destination stack
        :type dst_stack: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param dst_intfs: Name of the destination VNF interface to chain on
        :type dst_intfs: ``str``
        :return: flask.Response 200 if set up correctly else 500\
         also returns the cookie as dict {'cookie': value}
         501 if VNF or intfs does not exist
        :rtype: :class:`flask.Response`

        """
        # search for real names
        real_names = self._findNames(
            src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs)
        if not isinstance(real_names, tuple):
            # something went wrong
            return real_names

        container_src, container_dst, interface_src, interface_dst = real_names

        # check if both VNFs exist
        if not self.api.manage.check_vnf_intf_pair(
                container_src, interface_src):
            return Response(u"VNF %s or intfs %s does not exist" % (container_src, interface_src), status=501,
                            mimetype="application/json")
        if not self.api.manage.check_vnf_intf_pair(
                container_dst, interface_dst):
            return Response(u"VNF %s or intfs %s does not exist" % (container_dst, interface_dst), status=501,
                            mimetype="application/json")

        try:
            cookie = self.api.manage.network_action_start(container_src, container_dst, vnf_src_interface=interface_src,
                                                          vnf_dst_interface=interface_dst, bidirectional=True,
                                                          layer2=True)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200,
                            mimetype="application/json")

        except Exception as e:
            logging.exception(
                u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain",
                            status=500, mimetype="application/json")

    def post(self, src_dc, src_stack, src_vnf, src_intfs,
             dst_dc, dst_stack, dst_vnf, dst_intfs):
        """
         A post request to "/v1/chain/<src_dc>/<src_stack>/<src_vnf>/<src_intfs>/<dst_dc>/<dst_stack>/<dst_vnf>/<dst_intfs>"
         will create a chain between two interfaces at the specified vnfs.
         The POST data contains the path like this.
         { "path": ["dc1.s1", "s1", "dc4.s1"]}
         path specifies the destination vnf and interface and contains a list of switches
         that the path traverses. The path may not contain single hop loops like:
         [s1, s2, s1].
         This is a limitation of Ryu, as Ryu does not allow the `INPUT_PORT` action!

        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param src_intfs: Name of the source VNF interface to chain on
        :type src_intfs: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param dst_intfs: Name of the destination VNF interface to chain on
        :type dst_intfs: ``str``
        :return: flask.Response 200 if set up correctly else 500 also returns the cookie as dict {'cookie': value}
         501 if vnf / intfs do not exist
        :rtype: :class:`flask.Response`

        """
        if request.is_json:
            path = request.json.get('path')
            layer2 = request.json.get('layer2', True)
        else:
            path = None
            layer2 = True

        # search for real names
        real_names = self._findNames(
            src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs)
        if not isinstance(real_names, tuple):
            # something went wrong
            return real_names

        container_src, container_dst, interface_src, interface_dst = real_names

        try:
            cookie = self.api.manage.network_action_start(container_src, container_dst, vnf_src_interface=interface_src,
                                                          vnf_dst_interface=interface_dst, bidirectional=True,
                                                          path=path, layer2=layer2)
            resp = {'cookie': cookie}
            return Response(json.dumps(resp), status=200,
                            mimetype="application/json")

        except Exception as e:
            logging.exception(
                u"%s: Error setting up the chain.\n %s" % (__name__, e))
            return Response(u"Error setting up the chain",
                            status=500, mimetype="application/json")

    def delete(self, src_dc, src_stack, src_vnf, src_intfs,
               dst_dc, dst_stack, dst_vnf, dst_intfs):
        """
        A DELETE request to "/v1/chain/<src_dc>/<src_stack>/<src_vnf>/<src_intfs>/<dst_dc>/<dst_stack>/<dst_vnf>/<dst_intfs>"
        will delete a previously created chain.

        :param src_dc: Name of the source datacenter
        :type src_dc: `str`
        :param src_stack: Name of the source stack
        :type src_stack: `str`
        :param src_vnf: Name of the source VNF
        :type src_vnf: ``str``
        :param src_intfs: Name of the source VNF interface to chain on
        :type src_intfs: ``str``
        :param dst_dc: Name of the destination datacenter
        :type dst_dc: ``str``
        :param dst_stack: Name of the destination stack
        :type dst_stack: ``str``
        :param dst_vnf: Name of the destination VNF
        :type dst_vnf: ``str``
        :param dst_intfs: Name of the destination VNF interface to chain on
        :type dst_intfs: ``str``
        :return: flask.Response 200 if set up correctly else 500\
         also returns the cookie as dict {'cookie': value}
         501 if one of the VNF / intfs does not exist
        :rtype: :class:`flask.Response`

        """
        # search for real names
        real_names = self._findNames(
            src_dc, src_stack, src_vnf, src_intfs, dst_dc, dst_stack, dst_vnf, dst_intfs)
        if not isinstance(real_names, tuple):
            # something went wrong, real_names is a Response object
            return real_names

        container_src, container_dst, interface_src, interface_dst = real_names

        try:
            cookie = self.api.manage.network_action_stop(container_src, container_dst, vnf_src_interface=interface_src,
                                                         vnf_dst_interface=interface_dst, bidirectional=True)
            return Response(json.dumps(cookie), status=200,
                            mimetype="application/json")
        except Exception as e:
            logging.exception(
                u"%s: Error deleting the chain.\n %s" % (__name__, e))
            return Response(u"Error deleting the chain",
                            status=500, mimetype="application/json")

    # Tries to find real container and interface names according to heat template names
    # Returns a tuple of 4 or a Response object
    def _findNames(self, src_dc, src_stack, src_vnf, src_intfs,
                   dst_dc, dst_stack, dst_vnf, dst_intfs):
        # search for datacenters
        if src_dc not in self.api.manage.net.dcs or dst_dc not in self.api.manage.net.dcs:
            return Response(u"At least one DC does not exist",
                            status=500, mimetype="application/json")
        dc_src = self.api.manage.net.dcs[src_dc]
        dc_dst = self.api.manage.net.dcs[dst_dc]
        # search for related OpenStackAPIs
        api_src = None
        api_dst = None
        from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            if api.compute.dc == dc_src:
                api_src = api
            if api.compute.dc == dc_dst:
                api_dst = api
        if api_src is None or api_dst is None:
            return Response(u"At least one OpenStackAPI does not exist",
                            status=500, mimetype="application/json")
        # search for stacks
        stack_src = None
        stack_dst = None
        for stack in api_src.compute.stacks.values():
            if stack.stack_name == src_stack:
                stack_src = stack
        for stack in api_dst.compute.stacks.values():
            if stack.stack_name == dst_stack:
                stack_dst = stack
        if stack_src is None or stack_dst is None:
            return Response(u"At least one Stack does not exist",
                            status=500, mimetype="application/json")
        # search for servers
        server_src = None
        server_dst = None
        for server in stack_src.servers.values():
            if server.template_name == src_vnf:
                server_src = server
                break
        for server in stack_dst.servers.values():
            if server.template_name == dst_vnf:
                server_dst = server
                break
        if server_src is None or server_dst is None:
            return Response(u"At least one VNF does not exist",
                            status=500, mimetype="application/json")

        container_src = server_src.name
        container_dst = server_dst.name

        # search for ports
        port_src = None
        port_dst = None
        if src_intfs in server_src.port_names:
            port_src = stack_src.ports[src_intfs]
        if dst_intfs in server_dst.port_names:
            port_dst = stack_dst.ports[dst_intfs]
        if port_src is None or port_dst is None:
            return Response(u"At least one Port does not exist",
                            status=500, mimetype="application/json")

        interface_src = port_src.intf_name
        interface_dst = port_dst.intf_name

        return container_src, container_dst, interface_src, interface_dst


class BalanceHostDcStack(Resource):
    """
    Handles requests to "/v1/lb/<src_dc>/<src_stack>/<vnf_src_name>/<vnf_src_interface>"
    Sets up LoadBalancers for VNFs that are belonging to a certain stack.
    """

    def __init__(self, api):
        self.api = api

    def post(self, src_dc, src_stack, vnf_src_name, vnf_src_interface):
        """
        A POST request to "/v1/lb/<src_dc>/<src_stack>/<vnf_src_name>/<vnf_src_interface>"
        will set up a loadbalancer. The target VNFs and interfaces are in the post data.

        :Example:
            See :class:`heat.chain_api.BalanceHost.post`

        :param src_dc: Name of the source VNF
        :type src_dc: ``str``
        :param src_stack: Name of the source VNF interface to chain on
        :type src_stack: ``str``
         * src_stack == "floating" sets up a new floating node, so only use this name if you know what you are doing.
        :param vnf_src_name:
        :type vnf_src_name: ``str``
        :param vnf_src_interface:
        :type vnf_src_interface: ``str``
        :return: flask.Response 200 if set up correctly else 500
        :rtype: :class:`flask.Response`

        """
        try:
            req = request.json
            if req is None or len(req) == 0 or "dst_vnf_interfaces" not in req:
                return Response(u"You have to specify destination vnfs via the POST data.",
                                status=500, mimetype="application/json")

            dst_vnfs = req.get('dst_vnf_interfaces')
            container_src = None
            interface_src = None

            # check src vnf/port
            if src_stack != "floating":
                real_src = self._findName(
                    src_dc, src_stack, vnf_src_name, vnf_src_interface)
                if not isinstance(real_src, tuple):
                    # something went wrong, real_src is a Response object
                    return real_src

                container_src, interface_src = real_src

            real_dst_dict = {}
            for dst_vnf in dst_vnfs:
                dst_dc = dst_vnf.get('pop', None)
                dst_stack = dst_vnf.get('stack', None)
                dst_server = dst_vnf.get('server', None)
                dst_port = dst_vnf.get('port', None)
                if dst_dc is not None and dst_stack is not None and dst_server is not None and dst_port is not None:
                    real_dst = self._findName(
                        dst_dc, dst_stack, dst_server, dst_port)
                    if not isinstance(real_dst, tuple):
                        # something went wrong, real_dst is a Response object
                        return real_dst
                    real_dst_dict[real_dst[0]] = real_dst[1]

            input_object = {"dst_vnf_interfaces": real_dst_dict,
                            "path": req.get("path", None)}

            if src_stack != "floating":
                self.api.manage.add_loadbalancer(
                    container_src, interface_src, lb_data=input_object)
                return Response(u"Loadbalancer set up at %s:%s" % (container_src, interface_src),
                                status=200, mimetype="application/json")
            else:
                cookie, floating_ip = self.api.manage.add_floating_lb(
                    src_dc, lb_data=input_object)

                return Response(json.dumps({"cookie": "%d" % cookie, "floating_ip": "%s" % floating_ip}),
                                status=200, mimetype="application/json")

        except Exception as e:
            logging.exception(u"%s: Error setting up the loadbalancer at %s %s %s:%s.\n %s" %
                              (__name__, src_dc, src_stack, vnf_src_name, vnf_src_interface, e))
            return Response(u"%s: Error setting up the loadbalancer at %s %s %s:%s.\n %s" %
                            (__name__, src_dc, src_stack, vnf_src_name,
                             vnf_src_interface, e), status=500,
                            mimetype="application/json")

    def delete(self, src_dc, src_stack, vnf_src_name, vnf_src_interface):
        """
        Will delete a load balancer that sits behind a specified interface at a vnf for a specific stack

        :param src_dc: Name of the source VNF
        :type src_dc: ``str``
        :param src_stack: Name of the source VNF interface to chain on
        :type src_stack: ``str``
        :param vnf_src_name:
        :type vnf_src_name: ``str``
        :param vnf_src_interface:
        :type vnf_src_interface: ``str``
        :return: flask.Response 200 if set up correctly else 500
        :rtype: :class:`flask.Response`

        """
        try:
            # check src vnf/port
            if src_stack != "floating":
                real_src = self._findName(
                    src_dc, src_stack, vnf_src_name, vnf_src_interface)
                if not isinstance(real_src, tuple):
                    # something went wrong, real_src is a Response object
                    return real_src

                container_src, interface_src = real_src

                self.api.manage.delete_loadbalancer(
                    container_src, interface_src)
                return Response(u"Loadbalancer deleted at %s:%s" % (vnf_src_name, vnf_src_interface),
                                status=200, mimetype="application/json")
            else:
                cookie = vnf_src_name
                self.api.manage.delete_floating_lb(cookie)
                return Response(u"Floating loadbalancer with cookie %s deleted" % (cookie),
                                status=200, mimetype="application/json")

        except Exception as e:
            logging.exception(u"%s: Error deleting the loadbalancer at %s %s %s%s.\n %s" %
                              (__name__, src_dc, src_stack, vnf_src_name, vnf_src_interface, e))
            return Response(u"%s: Error deleting the loadbalancer at %s %s %s%s." %
                            (__name__, src_dc, src_stack, vnf_src_name,
                             vnf_src_interface), status=500,
                            mimetype="application/json")

    # Tries to find real container and port name according to heat template names
    # Returns a string or a Response object
    def _findName(self, dc, stack, vnf, port):
        # search for datacenters
        if dc not in self.api.manage.net.dcs:
            return Response(u"DC does not exist", status=500,
                            mimetype="application/json")
        dc_real = self.api.manage.net.dcs[dc]
        # search for related OpenStackAPIs
        api_real = None
        from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
        for api in OpenstackApiEndpoint.dc_apis:
            if api.compute.dc == dc_real:
                api_real = api
        if api_real is None:
            return Response(u"OpenStackAPI does not exist",
                            status=500, mimetype="application/json")
        # search for stacks
        stack_real = None
        for stackObj in api_real.compute.stacks.values():
            if stackObj.stack_name == stack:
                stack_real = stackObj
        if stack_real is None:
            return Response(u"Stack does not exist", status=500,
                            mimetype="application/json")
        # search for servers
        server_real = None
        for server in stack_real.servers.values():
            if server.template_name == vnf:
                server_real = server
                break
        if server_real is None:
            return Response(u"VNF does not exist", status=500,
                            mimetype="application/json")

        container_real = server_real.name

        # search for ports
        port_real = None
        if port in server_real.port_names:
            port_real = stack_real.ports[port]
        if port_real is None:
            return Response(u"At least one Port does not exist",
                            status=500, mimetype="application/json")

        interface_real = port_real.intf_name

        return container_real, interface_real


class BalanceHost(Resource):
    """
    Handles requests at "/v1/lb/<vnf_src_name>/<vnf_src_interface>"
    to set up or delete Load Balancers.
    """

    def __init__(self, api):
        self.api = api

    def post(self, vnf_src_name, vnf_src_interface):
        """
        Will set up a Load balancer behind an interface at a specified vnf
        We need both to avoid naming conflicts as interface names are not unique

        :param vnf_src_name: Name of the source VNF
        :type vnf_src_name: ``str``
        :param vnf_src_interface: Name of the source VNF interface to chain on
        :type vnf_src_interface: ``str``
        :return: flask.Response 200 if set up correctly else 500
         501 if VNF or intfs does not exist
        :rtype: :class:`flask.Response`

        """
        try:
            req = request.json
            if req is None or len(req) == 0 or "dst_vnf_interfaces" not in req:
                return Response(u"You have to specify destination vnfs via the POST data.",
                                status=500, mimetype="application/json")

            if vnf_src_name != "floating":
                # check if VNF exist
                if not self.api.manage.check_vnf_intf_pair(
                        vnf_src_name, vnf_src_interface):
                    return Response(u"VNF %s or intfs %s does not exist" % (vnf_src_name, vnf_src_interface),
                                    status=501,
                                    mimetype="application/json")
                self.api.manage.add_loadbalancer(
                    vnf_src_name, vnf_src_interface, lb_data=req)

                return Response(u"Loadbalancer set up at %s:%s" % (vnf_src_name, vnf_src_interface),
                                status=200, mimetype="application/json")
            else:
                cookie, floating_ip = self.api.manage.add_floating_lb(
                    vnf_src_interface, lb_data=req)

                return Response(json.dumps({"cookie": "%d" % cookie, "floating_ip": "%s" % floating_ip}),
                                status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error setting up the loadbalancer at %s:%s.\n %s" %
                              (__name__, vnf_src_name, vnf_src_interface, e))
            return Response(u"%s: Error setting up the loadbalancer at %s:%s.\n %s" %
                            (__name__, vnf_src_name, vnf_src_interface, e), status=500, mimetype="application/json")

    def delete(self, vnf_src_name, vnf_src_interface):
        """
        Will delete a load balancer that sits behind a specified interface at a vnf

        :param vnf_src_name: Name of the source VNF
        :type vnf_src_name: ``str``
        :param vnf_src_interface: Name of the source VNF interface to chain on
        :type vnf_src_interface: ``str``
        :return: flask.Response 200 if set up correctly else 500
         501 if VNF or intfs does not exist
        :rtype: :class:`flask.Response`

        """
        # check if VNF exist
        if not self.api.manage.check_vnf_intf_pair(
                vnf_src_name, vnf_src_interface):
            return Response(u"VNF %s or intfs %s does not exist" % (vnf_src_name, vnf_src_interface), status=501,
                            mimetype="application/json")
        try:
            logging.debug("Deleting loadbalancer at %s: interface: %s" %
                          (vnf_src_name, vnf_src_interface))
            net = self.api.manage.net

            if vnf_src_name != "floating":
                # check if VNF exists
                if vnf_src_name not in net:
                    return Response(u"Source VNF or interface can not be found." % vnf_src_name,
                                    status=404, mimetype="application/json")

                self.api.manage.delete_loadbalancer(
                    vnf_src_name, vnf_src_interface)

                return Response(u"Loadbalancer deleted at %s:%s" % (vnf_src_name, vnf_src_interface),
                                status=200, mimetype="application/json")
            else:
                cookie = vnf_src_name
                self.api.manage.delete_floating_lb(cookie)
                return Response(u"Floating loadbalancer with cookie %s removed" % (cookie),
                                status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error deleting the loadbalancer at %s%s.\n %s" %
                              (__name__, vnf_src_name, vnf_src_interface, e))
            return Response(u"%s: Error deleting the loadbalancer at %s%s." %
                            (__name__, vnf_src_name, vnf_src_interface), status=500, mimetype="application/json")


class QueryTopology(Resource):
    """
    Handles requests at "/v1/topo/"
    """

    def __init__(self, api):
        self.api = api

    def get(self):
        """
        Answers GET requests for the current network topology at "/v1/topo".
        This will only return switches and datacenters and ignore currently deployed VNFs.

        :return: 200 if successful with the network graph as json dict, else 500

        """
        try:
            logging.debug("Querying topology")
            graph = self.api.manage.net.DCNetwork_graph
            net = self.api.manage.net
            # root node is nodes
            topology = {"nodes": list()}

            for n in graph:
                # remove root node as well as the floating switch fs1
                if n != "root" and n != "fs1":
                    # we only want to return switches!
                    if not isinstance(net[n], OVSSwitch):
                        continue
                    node = dict()

                    # get real datacenter label
                    for dc in self.api.manage.net.dcs.values():
                        if str(dc.switch) == str(n):
                            node["name"] = str(n)
                            node["type"] = "Datacenter"
                            node["label"] = str(dc.label)
                            break

                    # node is not a datacenter. It has to be a switch
                    if node.get("type", "") != "Datacenter":
                        node["name"] = str(n)
                        node["type"] = "Switch"

                    node["links"] = list()
                    # add links to the topology
                    for graph_node, data in graph[n].items():
                        # only add links to the topology that connect switches
                        if isinstance(net[graph_node], OVSSwitch):
                            # we allow multiple edges between switches, so add them all
                            # with their unique keys
                            link = copy.copy(data)
                            for edge in link:
                                # do not add any links to the floating switch
                                # to the topology!
                                if graph_node == "fs1":
                                    continue
                                # the translator wants everything as a string!
                                for key, value in link[edge].items():
                                    link[edge][key] = str(value)
                                # name of the destination
                                link[edge]["name"] = graph_node
                                node["links"].append(link)

                    topology["nodes"].append(node)

            return Response(json.dumps(topology),
                            status=200, mimetype="application/json")
        except Exception as e:
            logging.exception(u"%s: Error querying topology.\n %s" %
                              (__name__, e))
            return Response(u"%s: Error querying topology.\n %s" %
                            (__name__, e), status=500, mimetype="application/json")
