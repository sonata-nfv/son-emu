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
from flask_restful import Resource
from flask import request, Response
from emuvim.api.openstack.openstack_dummies.base_openstack_dummy import \
    BaseOpenstackDummy
from datetime import datetime
import emuvim.api.openstack.openstack_dummies.neutron_sfc_dummy_api as SFC
import logging
import json
import uuid
import copy

LOG = logging.getLogger("api.openstack.neutron")


class NeutronDummyApi(BaseOpenstackDummy):
    def __init__(self, ip, port, compute):
        super(NeutronDummyApi, self).__init__(ip, port)
        self.compute = compute

        # create default networks (OSM usually assumes to have these
        # pre-configured)
        self.compute.create_network("mgmt")
        self.compute.create_network("mgmtnet")

        self.api.add_resource(NeutronListAPIVersions, "/")
        self.api.add_resource(NeutronShowAPIv2Details, "/v2.0")
        self.api.add_resource(NeutronListNetworks, "/v2.0/networks.json", "/v2.0/networks",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronShowNetwork, "/v2.0/networks/<network_id>.json", "/v2.0/networks/<network_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronCreateNetwork, "/v2.0/networks.json", "/v2.0/networks",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronUpdateNetwork, "/v2.0/networks/<network_id>.json", "/v2.0/networks/<network_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronDeleteNetwork, "/v2.0/networks/<network_id>.json", "/v2.0/networks/<network_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronListSubnets, "/v2.0/subnets.json", "/v2.0/subnets",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronShowSubnet, "/v2.0/subnets/<subnet_id>.json", "/v2.0/subnets/<subnet_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronCreateSubnet, "/v2.0/subnets.json", "/v2.0/subnets",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronUpdateSubnet, "/v2.0/subnets/<subnet_id>.json", "/v2.0/subnets/<subnet_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronDeleteSubnet, "/v2.0/subnets/<subnet_id>.json", "/v2.0/subnets/<subnet_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronListPorts, "/v2.0/ports.json", "/v2.0/ports",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronShowPort, "/v2.0/ports/<port_id>.json", "/v2.0/ports/<port_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronCreatePort, "/v2.0/ports.json", "/v2.0/ports",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronUpdatePort, "/v2.0/ports/<port_id>.json", "/v2.0/ports/<port_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronDeletePort, "/v2.0/ports/<port_id>.json", "/v2.0/ports/<port_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NeutronAddFloatingIp, "/v2.0/floatingips.json", "/v2.0/floatingips",
                              resource_class_kwargs={'api': self})

        # Service Function Chaining (SFC) API
        self.api.add_resource(SFC.PortPairsCreate, "/v2.0/sfc/port_pairs.json", "/v2.0/sfc/port_pairs",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairsUpdate, "/v2.0/sfc/port_pairs/<pair_id>.json",
                              "/v2.0/sfc/port_pairs/<pair_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairsDelete, "/v2.0/sfc/port_pairs/<pair_id>.json",
                              "/v2.0/sfc/port_pairs/<pair_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairsList, "/v2.0/sfc/port_pairs.json", "/v2.0/sfc/port_pairs",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairsShow, "/v2.0/sfc/port_pairs/<pair_id>.json",
                              "/v2.0/sfc/port_pairs/<pair_id>",
                              resource_class_kwargs={'api': self})

        self.api.add_resource(SFC.PortPairGroupCreate, "/v2.0/sfc/port_pair_groups.json", "/v2.0/sfc/port_pair_groups",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairGroupUpdate, "/v2.0/sfc/port_pair_groups/<group_id>.json",
                              "/v2.0/sfc/port_pair_groups/<group_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairGroupDelete, "/v2.0/sfc/port_pair_groups/<group_id>.json",
                              "/v2.0/sfc/port_pair_groups/<group_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairGroupList, "/v2.0/sfc/port_pair_groups.json", "/v2.0/sfc/port_pair_groups",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortPairGroupShow, "/v2.0/sfc/port_pair_groups/<group_id>.json",
                              "/v2.0/sfc/port_pair_groups/<group_id>",
                              resource_class_kwargs={'api': self})

        self.api.add_resource(SFC.FlowClassifierCreate, "/v2.0/sfc/flow_classifiers.json", "/v2.0/sfc/flow_classifiers",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.FlowClassifierUpdate, "/v2.0/sfc/flow_classifiers/<flow_classifier_id>.json",
                              "/v2.0/sfc/flow_classifiers/<flow_classifier_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.FlowClassifierDelete, "/v2.0/sfc/flow_classifiers/<flow_classifier_id>.json",
                              "/v2.0/sfc/flow_classifiers/<flow_classifier_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.FlowClassifierList, "/v2.0/sfc/flow_classifiers.json", "/v2.0/sfc/flow_classifiers",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.FlowClassifierShow, "/v2.0/sfc/flow_classifiers/<flow_classifier_id>.json",
                              "/v2.0/sfc/flow_classifiers/<flow_classifier_id>",
                              resource_class_kwargs={'api': self})

        self.api.add_resource(SFC.PortChainCreate, "/v2.0/sfc/port_chains.json", "/v2.0/sfc/port_chains",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortChainUpdate, "/v2.0/sfc/port_chains/<chain_id>.json",
                              "/v2.0/sfc/port_chains/<chain_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortChainDelete, "/v2.0/sfc/port_chains/<chain_id>.json",
                              "/v2.0/sfc/port_chains/<chain_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortChainList, "/v2.0/sfc/port_chains.json", "/v2.0/sfc/port_chains",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(SFC.PortChainShow, "/v2.0/sfc/port_chains/<chain_id>.json",
                              "/v2.0/sfc/port_chains/<chain_id>",
                              resource_class_kwargs={'api': self})


class NeutronListAPIVersions(Resource):
    def get(self):
        """
        Lists API versions.

        :return: Returns a json with API versions.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: Neutron - List API Versions")
        resp = dict()
        resp['versions'] = dict()

        versions = [{
            "status": "CURRENT",
            "id": "v2.0",
            "links": [
                {
                    "href": request.url_root + '/v2.0',
                    "rel": "self"
                }
            ]
        }]
        resp['versions'] = versions

        return Response(json.dumps(resp), status=200,
                        mimetype='application/json')


class NeutronShowAPIv2Details(Resource):
    def get(self):
        """
        Returns API details.

        :return: Returns a json with API details.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        resp = dict()

        resp['resources'] = dict()
        resp['resources'] = [{
            "links": [
                {
                    "href": request.url_root + 'v2.0/subnets',
                    "rel": "self"
                }
            ],
            "name": "subnet",
            "collection": "subnets"
        },
            {
                "links": [
                    {
                        "href": request.url_root + 'v2.0/networks',
                        "rel": "self"
                    }
                ],
                "name": "network",
                "collection": "networks"
        },
            {
                "links": [
                    {
                        "href": request.url_root + 'v2.0/ports',
                        "rel": "self"
                    }
                ],
                "name": "ports",
                "collection": "ports"
        }
        ]

        return Response(json.dumps(resp), status=200,
                        mimetype='application/json')


class NeutronListNetworks(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        """
        Lists all networks, used in son-emu. If a 'name' or one or more 'id's are specified, it will only list the
        network with the name, or the networks specified via id.

        :return: Returns a json response, starting with 'networks' as root node.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        # LOG.debug("ARGS: {}".format(request.args))
        try:
            if request.args.get('name'):
                tmp_network = NeutronShowNetwork(self.api)
                response = tmp_network.get_network(
                    request.args.get('name'), True)
                LOG.debug("{} RESPONSE (1): {}".format(
                    self.__class__.__name__, response))
                return response
            id_list = request.args.getlist('id')
            if len(id_list) == 1:
                tmp_network = NeutronShowNetwork(self.api)
                response = tmp_network.get_network(
                    request.args.get('id'), True)
                LOG.debug("{} RESPONSE (2): {}".format(
                    self.__class__.__name__, response))
                return response

            network_list = list()
            network_dict = dict()

            if len(id_list) == 0:
                for net in self.api.compute.nets.values():
                    tmp_network_dict = net.create_network_dict()
                    if tmp_network_dict not in network_list:
                        network_list.append(tmp_network_dict)
            else:
                for net in self.api.compute.nets.values():
                    if net.id in id_list:
                        tmp_network_dict = net.create_network_dict()
                        if tmp_network_dict not in network_list:
                            network_list.append(tmp_network_dict)

            network_dict["networks"] = network_list
            LOG.debug("{} RESPONSE (3): {}".format(
                self.__class__.__name__, network_dict))
            return Response(json.dumps(network_dict),
                            status=200, mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: List networks exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronShowNetwork(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, network_id):
        """
        Returns the network, specified via 'network_id'.

        :param network_id: The unique ID string of the network.
        :type network_id: ``str``
        :return: Returns a json response, starting with 'network' as root node and one network description.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return self.get_network(network_id, False)

    def get_network(self, network_name_or_id, as_list):
        """
        Returns one network description of the network, specified via 'network_name_or_id'.

        :param network_name_or_id: The indicator string, which specifies the requested network.
        :type network_name_or_id: ``str``
        :param as_list: Determines if the network description should start with the root node 'network' or 'networks'.
        :type as_list: ``bool``
        :return: Returns a json response, with one network description.
        :rtype: :class:`flask.response`
        """
        try:
            net = self.api.compute.find_network_by_name_or_id(
                network_name_or_id)
            if net is None:
                return Response(u'Network not found.\n',
                                status=404, mimetype='application/json')

            tmp_network_dict = net.create_network_dict()
            tmp_dict = dict()
            if as_list:
                tmp_dict["networks"] = [tmp_network_dict]
            else:
                tmp_dict["network"] = tmp_network_dict

            return Response(json.dumps(tmp_dict), status=200,
                            mimetype='application/json')

        except Exception as ex:
            logging.exception("Neutron: Show network exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronCreateNetwork(Resource):
    def __init__(self, api):
        self.api = api

    def post(self):
        """
        Creates a network with the name, specified within the request under ['network']['name'].

        :return: * 400, if the network already exists.
            * 500, if any exception occurred while creation.
            * 201, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            network_dict = json.loads(request.data)
            name = network_dict['network']['name']
            net = self.api.compute.find_network_by_name_or_id(name)
            if net is not None:
                return Response('Network already exists.\n',
                                status=400, mimetype='application/json')

            net = self.api.compute.create_network(name)
            return Response(json.dumps(
                {"network": net.create_network_dict()}), status=201, mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Create network excepiton.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronUpdateNetwork(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, network_id):  # TODO currently only the name will be changed
        """
        Updates the existing network with the given parameters.

        :param network_id: The indicator string, which specifies the requested network.
        :type network_id: ``str``
        :return: * 404, if the network could not be found.
            * 500, if any exception occurred while updating the network.
            * 200, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s PUT" % str(self.__class__.__name__))
        try:
            if network_id in self.api.compute.nets:
                net = self.api.compute.nets[network_id]
                network_dict = json.loads(request.data)

                if "status" in network_dict["network"]:
                    net.status = network_dict["network"]["status"]
                if "subnets" in network_dict["network"]:
                    pass  # tmp_network_dict["subnets"] = None
                if "name" in network_dict["network"] and net.name != network_dict["network"]["name"]:
                    net.name = network_dict["network"]["name"]
                if "admin_state_up" in network_dict["network"]:
                    pass  # tmp_network_dict["admin_state_up"] = True
                if "tenant_id" in network_dict["network"]:
                    # tmp_network_dict["tenant_id"] = "c1210485b2424d48804aad5d39c61b8f"
                    pass
                if "shared" in network_dict["network"]:
                    pass  # tmp_network_dict["shared"] = False

                return Response(json.dumps(network_dict),
                                status=200, mimetype='application/json')

            return Response('Network not found.\n', status=404,
                            mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: Show networks exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronDeleteNetwork(Resource):
    def __init__(self, api):
        self.api = api

    def delete(self, network_id):
        """
        Deletes the specified network and all its subnets.

        :param network_id: The indicator string, which specifies the requested network.
        :type network_id: ``str``
        :return: * 404, if the network or the subnet could not be removed.
            * 500, if any exception occurred while deletion.
            * 204, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            if network_id not in self.api.compute.nets:
                return Response('Could not find network. (' + network_id + ')\n',
                                status=404, mimetype='application/json')

            net = self.api.compute.nets[network_id]
            delete_subnet = NeutronDeleteSubnet(self.api)
            resp = delete_subnet.delete(net.subnet_id)

            if '204' not in resp.status and '404' not in resp.status:
                return resp

            self.api.compute.delete_network(network_id)

            return Response('', status=204, mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Delete network exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronListSubnets(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        """
        Lists all subnets, used in son-emu. If a 'name' or one or more 'id's are specified, it will only list the
        subnet with the name, or the subnets specified via id.

        :return: Returns a json response, starting with 'subnets' as root node.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            if request.args.get('name'):
                show_subnet = NeutronShowSubnet(self.api)
                return show_subnet.get_subnet(request.args.get('name'), True)
            id_list = request.args.getlist('id')
            if len(id_list) == 1:
                show_subnet = NeutronShowSubnet(self.api)
                return show_subnet.get_subnet(id_list[0], True)

            subnet_list = list()
            subnet_dict = dict()

            if len(id_list) == 0:
                for net in self.api.compute.nets.values():
                    if net.subnet_id is not None:
                        tmp_subnet_dict = net.create_subnet_dict()
                        subnet_list.append(tmp_subnet_dict)
            else:
                for net in self.api.compute.nets.values():
                    if net.subnet_id in id_list:
                        tmp_subnet_dict = net.create_subnet_dict()
                        subnet_list.append(tmp_subnet_dict)

            subnet_dict["subnets"] = subnet_list

            return Response(json.dumps(subnet_dict), status=200,
                            mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: List subnets exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronShowSubnet(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, subnet_id):
        """
        Returns the subnet, specified via 'subnet_id'.

        :param subnet_id: The unique ID string of the subnet.
        :type subnet_id: ``str``
        :return: Returns a json response, starting with 'subnet' as root node and one subnet description.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return self.get_subnet(subnet_id, False)

    def get_subnet(self, subnet_name_or_id, as_list):
        """
        Returns one subnet description of the subnet, specified via 'subnet_name_or_id'.

        :param subnet_name_or_id: The indicator string, which specifies the requested subnet.
        :type subnet_name_or_id: ``str``
        :param as_list: Determines if the subnet description should start with the root node 'subnet' or 'subnets'.
        :type as_list: ``bool``
        :return: Returns a json response, with one subnet description.
        :rtype: :class:`flask.response`
        """
        try:
            for net in self.api.compute.nets.values():
                if net.subnet_id == subnet_name_or_id or net.subnet_name == subnet_name_or_id:
                    tmp_subnet_dict = net.create_subnet_dict()
                    tmp_dict = dict()
                    if as_list:
                        tmp_dict["subnets"] = [tmp_subnet_dict]
                    else:
                        tmp_dict["subnet"] = tmp_subnet_dict
                    return Response(json.dumps(tmp_dict),
                                    status=200, mimetype='application/json')

            return Response('Subnet not found. (' + subnet_name_or_id +
                            ')\n', status=404, mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: Show subnet exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronCreateSubnet(Resource):
    def __init__(self, api):
        self.api = api

    def post(self):
        """
        Creates a subnet with the name, specified within the request under ['subnet']['name'].

        :return: * 400, if the 'CIDR' format is wrong or it does not exist.
            * 404, if the network was not found.
            * 409, if the corresponding network already has one subnet.
            * 500, if any exception occurred while creation and
            * 201, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            subnet_dict = json.loads(request.data)
            net = self.api.compute.find_network_by_name_or_id(
                subnet_dict['subnet']['network_id'])

            if net is None:
                return Response('Could not find network.\n',
                                status=404, mimetype='application/json')

            net.subnet_name = subnet_dict["subnet"].get(
                'name', str(net.name) + '-sub')
            if net.subnet_id is not None:
                LOG.error(
                    "Only one subnet per network is supported: {}".format(net.subnet_id))
                return Response('Only one subnet per network is supported\n',
                                status=409, mimetype='application/json')

            if "id" in subnet_dict["subnet"]:
                net.subnet_id = subnet_dict["subnet"]["id"]
            else:
                net.subnet_id = str(uuid.uuid4())
            import emuvim.api.openstack.ip_handler as IP
            net.set_cidr(IP.get_new_cidr(net.subnet_id))

            if "tenant_id" in subnet_dict["subnet"]:
                pass
            if "allocation_pools" in subnet_dict["subnet"]:
                pass
            if "gateway_ip" in subnet_dict["subnet"]:
                net.gateway_ip = subnet_dict["subnet"]["gateway_ip"]
            if "ip_version" in subnet_dict["subnet"]:
                pass
            if "enable_dhcp" in subnet_dict["subnet"]:
                pass

            return Response(json.dumps(
                {'subnet': net.create_subnet_dict()}), status=201, mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: Create network excepiton.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronUpdateSubnet(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, subnet_id):
        """
        Updates the existing subnet with the given parameters.

        :param subnet_id: The indicator string, which specifies the requested subnet.
        :type subnet_id: ``str``
        :return: * 404, if the network could not be found.
            * 500, if any exception occurred while updating the network.
            * 200, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s PUT" % str(self.__class__.__name__))
        try:
            for net in self.api.compute.nets.values():
                if net.subnet_id == subnet_id:
                    subnet_dict = json.loads(request.data)

                    if "name" in subnet_dict["subnet"]:
                        net.subnet_name = subnet_dict["subnet"]["name"]
                    if "network_id" in subnet_dict["subnet"]:
                        net.id = subnet_dict["subnet"]["network_id"]
                    if "tenant_id" in subnet_dict["subnet"]:
                        pass
                    if "allocation_pools" in subnet_dict["subnet"]:
                        pass
                    if "gateway_ip" in subnet_dict["subnet"]:
                        net.gateway_ip = subnet_dict["subnet"]["gateway_ip"]
                    if "ip_version" in subnet_dict["subnet"]:
                        pass
                    if "cidr" in subnet_dict["subnet"]:
                        net.set_cidr(subnet_dict["subnet"]["cidr"])
                    if "id" in subnet_dict["subnet"]:
                        net.subnet_id = subnet_dict["subnet"]["id"]
                    if "enable_dhcp" in subnet_dict["subnet"]:
                        pass

                    net.subnet_update_time = str(datetime.now())
                    tmp_dict = {'subnet': net.create_subnet_dict()}
                    return Response(json.dumps(tmp_dict),
                                    status=200, mimetype='application/json')

            return Response('Network not found.\n', status=404,
                            mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: Show networks exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronDeleteSubnet(Resource):
    def __init__(self, api):
        self.api = api

    def delete(self, subnet_id):
        """
        Deletes the specified subnet.

        :param subnet_id: The indicator string, which specifies the requested subnet.
        :type subnet_id: ``str``
        :return: * 404, if the subnet could not be removed.
            * 500, if any exception occurred while deletion.
            * 204, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            for net in self.api.compute.nets.values():
                if net.subnet_id == subnet_id:
                    for server in self.api.compute.computeUnits.values():
                        for port_name in server.port_names:
                            port = self.api.compute.find_port_by_name_or_id(
                                port_name)
                            if port is None:
                                LOG.warning(
                                    "Port search for {} returned None.".format(port_name))
                                continue
                            if port.net_name == net.name:
                                port.ip_address = None
                                self.api.compute.dc.net.removeLink(
                                    link=None,
                                    node1=self.api.compute.dc.containers[server.name],
                                    node2=self.api.compute.dc.switch)
                                port.net_name = None

                    net.delete_subnet()

                    return Response(
                        '', status=204, mimetype='application/json')

            return Response('Could not find subnet.',
                            status=404, mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Delete subnet exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronListPorts(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        """
        Lists all ports, used in son-emu. If a 'name' or one or more 'id's are specified, it will only list the
        port with the name, or the ports specified via id.

        :return: Returns a json response, starting with 'ports' as root node.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            if request.args.get('name'):
                show_port = NeutronShowPort(self.api)
                return show_port.get_port(request.args.get('name'), True)
            id_list = request.args.getlist('id')
            if len(id_list) == 1:
                show_port = NeutronShowPort(self.api)
                return show_port.get_port(request.args.get('id'), True)

            ports = self.api.compute.ports.values()
            if len(id_list) != 0:
                ports = filter(lambda port: port.id in id_list, ports)

            device_id = request.args.get('device_id')
            if device_id:
                server = self.api.compute.find_server_by_name_or_id(device_id)
                if not server:
                    raise RuntimeError("Unable to find server '%s' in order to return it's ports" % server)

                ports = filter(lambda port: (
                    any(
                        filter(
                            lambda server_port_name_or_id: (
                                port.id == server_port_name_or_id or port.name == server_port_name_or_id
                            ),
                            server.port_names
                        )
                    )
                ), ports)

            port_dict = dict()
            port_dict["ports"] = list(map(lambda x: x.create_port_dict(self.api.compute), ports))

            return Response(json.dumps(port_dict), status=200,
                            mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: List ports exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronShowPort(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, port_id):
        """
        Returns the port, specified via 'port_id'.

        :param port_id: The unique ID string of the network.
        :type port_id: ``str``
        :return: Returns a json response, starting with 'port' as root node and one network description.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return self.get_port(port_id, False)

    def get_port(self, port_name_or_id, as_list):
        """
        Returns one network description of the port, specified via 'port_name_or_id'.

        :param port_name_or_id: The indicator string, which specifies the requested port.
        :type port_name_or_id: ``str``
        :param as_list: Determines if the port description should start with the root node 'port' or 'ports'.
        :type as_list: ``bool``
        :return: Returns a json response, with one port description.
        :rtype: :class:`flask.response`
        """
        try:
            port = self.api.compute.find_port_by_name_or_id(port_name_or_id)
            if port is None:
                return Response('Port not found. (' + port_name_or_id + ')\n',
                                status=404, mimetype='application/json')
            tmp_port_dict = port.create_port_dict(self.api.compute)
            tmp_dict = dict()
            if as_list:
                tmp_dict["ports"] = [tmp_port_dict]
            else:
                tmp_dict["port"] = tmp_port_dict
            return Response(json.dumps(tmp_dict), status=200,
                            mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Show port exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronCreatePort(Resource):
    def __init__(self, api):
        self.api = api

    def post(self):
        """
        Creates a port with the name, specified within the request under ['port']['name'].

        :return: * 404, if the network could not be found.
            * 500, if any exception occurred while creation and
            * 201, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            port_dict = json.loads(request.data)
            net_id = port_dict['port']['network_id']

            if net_id not in self.api.compute.nets:
                return Response('Could not find network.\n',
                                status=404, mimetype='application/json')

            net = self.api.compute.nets[net_id]
            if 'name' in port_dict['port']:
                name = port_dict['port']['name']
            else:
                num_ports = len(self.api.compute.ports)
                name = "port:cp%s:man:%s" % (num_ports, str(uuid.uuid4()))

            port = self.api.compute.create_port(name)

            port.net_name = net.name
            port.ip_address = net.get_new_ip_address(name)

            if "admin_state_up" in port_dict["port"]:
                pass
            if "device_id" in port_dict["port"]:
                pass
            if "device_owner" in port_dict["port"]:
                pass
            if "fixed_ips" in port_dict["port"]:
                pass
            if "mac_address" in port_dict["port"]:
                port.mac_address = port_dict["port"]["mac_address"]
            if "status" in port_dict["port"]:
                pass
            if "tenant_id" in port_dict["port"]:
                pass

            # add the port to a stack if the specified network is a stack
            # network
            for stack in self.api.compute.stacks.values():
                for net in stack.nets.values():
                    if net.id == net_id:
                        stack.ports[name] = port

            return Response(json.dumps({'port': port.create_port_dict(self.api.compute)}), status=201,
                            mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Show port exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronUpdatePort(Resource):
    def __init__(self, api):
        self.api = api

    def put(self, port_id):
        """
        Updates the existing port with the given parameters.

        :param network_id: The indicator string, which specifies the requested port.
        :type network_id: ``str``
        :return: * 404, if the network could not be found.
            * 500, if any exception occurred while updating the network.
            * 200, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s PUT" % str(self.__class__.__name__))
        try:
            port_dict = json.loads(request.data)
            port = self.api.compute.find_port_by_name_or_id(port_id)
            if port is None:
                return Response("Port with id %s does not exists.\n" %
                                port_id, status=404, mimetype='application/json')
            old_port = copy.copy(port)

            stack = None
            for s in self.api.compute.stacks.values():
                for port in s.ports.values():
                    if port.id == port_id:
                        stack = s
            if "admin_state_up" in port_dict["port"]:
                pass
            if "device_id" in port_dict["port"]:
                pass
            if "device_owner" in port_dict["port"]:
                pass
            if "fixed_ips" in port_dict["port"]:
                pass
            if "id" in port_dict["port"]:
                port.id = port_dict["port"]["id"]
            if "mac_address" in port_dict["port"]:
                port.mac_address = port_dict["port"]["mac_address"]
            if "name" in port_dict["port"] and port_dict["port"]["name"] != port.name:
                port.set_name(port_dict["port"]["name"])
                if stack is not None:
                    if port.net_name in stack.nets:
                        stack.nets[port.net_name].update_port_name_for_ip_address(
                            port.ip_address, port.name)
                    stack.ports[port.name] = stack.ports[old_port.name]
                    del stack.ports[old_port.name]
            if "network_id" in port_dict["port"]:
                pass
            if "status" in port_dict["port"]:
                pass
            if "tenant_id" in port_dict["port"]:
                pass

            return Response(json.dumps({'port': port.create_port_dict(self.api.compute)}), status=200,
                            mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Update port exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronDeletePort(Resource):
    def __init__(self, api):
        self.api = api

    def delete(self, port_id):
        """
        Deletes the specified port.

        :param port_id: The indicator string, which specifies the requested port.
        :type port_id: ``str``
        :return: * 404, if the port could not be found.
            * 500, if any exception occurred while deletion.
            * 204, if everything worked out.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            port = self.api.compute.find_port_by_name_or_id(port_id)
            if port is None:
                return Response("Port with id %s does not exists.\n" %
                                port_id, status=404)
            stack = None
            for s in self.api.compute.stacks.values():
                for p in s.ports.values():
                    if p.id == port_id:
                        stack = s
            if stack is not None:
                if port.net_name in stack.nets:
                    stack.nets[port.net_name].withdraw_ip_address(
                        port.ip_address)
                for server in stack.servers.values():
                    try:
                        server.port_names.remove(port.name)
                    except ValueError:
                        pass

            # delete the port
            self.api.compute.delete_port(port.id)

            return Response('', status=204, mimetype='application/json')

        except Exception as ex:
            LOG.exception("Neutron: Delete port exception.")
            return Response(str(ex), status=500,
                            mimetype='application/json')


class NeutronAddFloatingIp(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        """
        Returns a Floating IP for a port.

        Currently ports are not mapped to individual IPs, but the
        (potentially shared) Docker external IP is returned.
        """
        port_id = request.args.get("port_id")
        if not port_id:
            message = "Neutron: List API for FloatingIPs is not implemented"
            LOG.exception(message)
            return Response(message, status=500,
                            mimetype='application/json')
        port = self.api.compute.find_port_by_name_or_id(port_id)
        ip = port.assigned_container.dcinfo["NetworkSettings"]["IPAddress"]
        resp = dict()
        resp["floatingips"] = [
            {'floating_ip_address': ip}
        ]
        return Response(json.dumps(resp), status=200,
                        mimetype='application/json')

    def post(self):
        """
        Adds a floating IP to neutron.

        :return: Returns a floating network description.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            # Fiddle with floating_network !
            req = json.loads(request.data)

            network_id = req["floatingip"]["floating_network_id"]
            net = self.api.compute.find_network_by_name_or_id(network_id)
            if net != self.api.manage.floating_network:
                return Response("You have to specify the existing floating network\n",
                                status=400, mimetype='application/json')

            port_id = req["floatingip"].get("port_id", None)
            port = self.api.compute.find_port_by_name_or_id(port_id)
            if port is not None:
                if port.net_name != self.api.manage.floating_network.name:
                    return Response("You have to specify a port in the floating network\n",
                                    status=400, mimetype='application/json')

                if port.floating_ip is not None:
                    return Response("We allow only one floating ip per port\n",
                                    status=400, mimetype='application/json')
            else:
                num_ports = len(self.api.compute.ports)
                name = "port:cp%s:fl:%s" % (num_ports, str(uuid.uuid4()))
                port = self.api.compute.create_port(name)
                port.net_name = net.name
                port.ip_address = net.get_new_ip_address(name)

            port.floating_ip = port.ip_address

            response = dict()
            resp = response["floatingip"] = dict()

            resp["floating_network_id"] = net.id
            resp["status"] = "ACTIVE"
            resp["id"] = net.id
            resp["port_id"] = port.id
            resp["floating_ip_address"] = port.floating_ip
            resp["fixed_ip_address"] = port.floating_ip

            return Response(json.dumps(response), status=200,
                            mimetype='application/json')
        except Exception as ex:
            LOG.exception("Neutron: Create FloatingIP exception %s.", ex)
            return Response(str(ex), status=500,
                            mimetype='application/json')
