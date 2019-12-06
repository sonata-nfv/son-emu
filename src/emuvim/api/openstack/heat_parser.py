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
# TODO remove when print is no longer needed for debugging
from __future__ import print_function
from emuvim.api.openstack.resources.router import Router
from datetime import datetime
import re
import sys
import uuid
import logging
import emuvim.api.openstack.ip_handler as IP


LOG = logging.getLogger("api.openstack.heat.parser")


class HeatParser:
    """
    The HeatParser will parse a heat dictionary and create a stack and its components, to instantiate it within son-emu.
    """

    def __init__(self, compute):
        self.description = None
        self.parameter_groups = None
        self.parameters = None
        self.resources = None
        self.outputs = None
        self.compute = compute
        self.bufferResource = list()

    def parse_input(self, input_dict, stack, dc_label, stack_update=False):
        """
        It will parse the input dictionary into the corresponding classes, which are then stored within the stack.

        :param input_dict: Dictionary with the template version and resources.
        :type input_dict: ``dict``
        :param stack: Reference of the stack that should finally contain all created classes.
        :type stack: :class:`heat.resources.stack`
        :param dc_label: String that contains the label of the used data center.
        :type dc_label: ``str``
        :param stack_update: Specifies if a new stack will be created or a older one will be updated
        :type stack_update: ``bool``
        :return: * *True*: If the template version is supported and all resources could be created.
                 * *False*: Else
        :rtype: ``bool``
        """
        if not self.check_template_version(
                str(input_dict['heat_template_version'])):
            print('Unsupported template version: ' + input_dict['heat_template_version'], file=sys.stderr)
            return False

        self.description = input_dict.get('description', None)
        self.parameter_groups = input_dict.get('parameter_groups', None)
        self.parameters = input_dict.get('parameters', None)
        self.resources = input_dict.get('resources', None)
        self.outputs = input_dict.get('outputs', None)
        # clear bufferResources
        self.bufferResource = list()

        for resource in self.resources.values():
            self.handle_resource(resource, stack, dc_label,
                                 stack_update=stack_update)

        # This loop tries to create all classes which had unresolved
        # dependencies.
        unresolved_resources_last_round = len(self.bufferResource) + 1
        while len(self.bufferResource) > 0 and unresolved_resources_last_round > len(
                self.bufferResource):
            unresolved_resources_last_round = len(self.bufferResource)
            number_of_items = len(self.bufferResource)
            while number_of_items > 0:
                self.handle_resource(self.bufferResource.pop(
                    0), stack, dc_label, stack_update=stack_update)
                number_of_items -= 1

        if len(self.bufferResource) > 0:
            print(str(len(self.bufferResource)) +
                  ' classes of the HOT could not be created, because the dependencies could not be found.')
            print("the problem classes are:")
            for br in self.bufferResource:
                print("class: %s" % str(br))
            return False
        return True

    def handle_resource(self, resource, stack, dc_label, stack_update=False):
        """
        This function will take a resource (from a heat template) and determines which type it is and creates
        the corresponding class, with its required parameters, for further calculations (like deploying the stack).
        If it is not possible to create the class, because of unresolved dependencies, it will buffer the resource
        within the 'self.bufferResource' list.

        :param resource: Dict which contains all important informations about the type and parameters.
        :type resource: ``dict``
        :param stack: Reference of the stack that should finally contain the created class.
        :type stack: :class:`heat.resources.stack`
        :param dc_label: String that contains the label of the used data center
        :type dc_label: ``str``
        :param stack_update: Specifies if a new stack will be created or a older one will be updated
        :type stack_update: ``bool``
        :return: void
        :rtype: ``None``
        """
        if "OS::Neutron::Net" in resource['type']:
            try:
                net_name = resource['properties']['name']
                if net_name not in stack.nets:
                    stack.nets[net_name] = self.compute.create_network(
                        net_name, True)

            except Exception as e:
                LOG.warning('Could not create Net: ' + str(e))
            return

        if 'OS::Neutron::Subnet' in resource['type'] and "Net" not in resource['type']:
            try:
                net_name = resource['properties']['network']['get_resource']
                if net_name not in stack.nets:
                    net = self.compute.create_network(net_name, stack_update)
                    stack.nets[net_name] = net
                else:
                    net = stack.nets[net_name]

                net.subnet_name = resource['properties']['name']
                if 'gateway_ip' in resource['properties']:
                    net.gateway_ip = resource['properties']['gateway_ip']
                net.subnet_id = resource['properties'].get(
                    'id', str(uuid.uuid4()))
                net.subnet_creation_time = str(datetime.now())
                if not stack_update:
                    net.set_cidr(IP.get_new_cidr(net.subnet_id))
            except Exception as e:
                LOG.warning('Could not create Subnet: ' + str(e))
            return

        if 'OS::Neutron::Port' in resource['type']:
            try:
                port_name = resource['properties']['name']
                if port_name not in stack.ports:
                    port = self.compute.create_port(port_name, stack_update)
                    stack.ports[port_name] = port
                else:
                    port = stack.ports[port_name]

                if str(resource['properties']['network']
                       ['get_resource']) in stack.nets:
                    net = stack.nets[resource['properties']
                                     ['network']['get_resource']]
                    if net.subnet_id is not None:
                        port.net_name = net.name
                        port.ip_address = net.get_new_ip_address(port.name)
                        return
            except Exception as e:
                LOG.warning('Could not create Port: ' + str(e))
            self.bufferResource.append(resource)
            return

        if 'OS::Nova::Server' in resource['type']:
            try:
                compute_name = str(dc_label) + '_' + str(stack.stack_name) + \
                    '_' + str(resource['properties']['name'])
                shortened_name = str(dc_label) + '_' + str(stack.stack_name) + '_' + \
                    self.shorten_server_name(
                        str(resource['properties']['name']), stack)
                nw_list = resource['properties']['networks']

                if shortened_name not in stack.servers:
                    server = self.compute.create_server(
                        shortened_name, stack_update)
                    stack.servers[shortened_name] = server
                else:
                    server = stack.servers[shortened_name]

                server.full_name = compute_name
                server.template_name = str(resource['properties']['name'])
                server.command = resource['properties'].get(
                    'command', '/bin/sh')
                server.image = resource['properties']['image']
                server.flavor = resource['properties']['flavor']

                for port in nw_list:
                    port_name = port['port']['get_resource']
                    # just create a port
                    # we don't know which network it belongs to yet, but the resource will appear later in a valid
                    # template
                    if port_name not in stack.ports:
                        stack.ports[port_name] = self.compute.create_port(
                            port_name, stack_update)
                    server.port_names.append(port_name)
                return
            except Exception as e:
                LOG.warning('Could not create Server: ' + str(e))
            return

        if 'OS::Neutron::RouterInterface' in resource['type']:
            try:
                router_name = None
                subnet_name = resource['properties']['subnet']['get_resource']

                if 'get_resource' in resource['properties']['router']:
                    router_name = resource['properties']['router']['get_resource']
                else:
                    router_name = resource['properties']['router']

                if router_name not in stack.routers:
                    stack.routers[router_name] = Router(router_name)

                for tmp_net in stack.nets.values():
                    if tmp_net.subnet_name == subnet_name:
                        stack.routers[router_name].add_subnet(subnet_name)
                        return
            except Exception as e:
                LOG.warning(
                    'Could not create RouterInterface: ' + e.__repr__())
            self.bufferResource.append(resource)
            return

        if 'OS::Neutron::FloatingIP' in resource['type']:
            try:
                port_name = resource['properties']['port_id']['get_resource']
                floating_network_id = resource['properties']['floating_network_id']
                if port_name not in stack.ports:
                    stack.ports[port_name] = self.compute.create_port(
                        port_name, stack_update)

                stack.ports[port_name].floating_ip = floating_network_id
            except Exception as e:
                LOG.warning('Could not create FloatingIP: ' + str(e))
            return

        if 'OS::Neutron::Router' in resource['type']:
            try:
                name = resource['properties']['name']
                if name not in stack.routers:
                    stack.routers[name] = Router(name)
            except Exception as e:
                print('Could not create Router: ' + str(e))
            return

        if 'OS::Heat::ResourceGroup' in resource['type']:
            try:
                embedded_resource = resource['properties']['resource_def']
                LOG.debug("Found resource in resource group: {}".format(
                    embedded_resource))
                # recursively parse embedded resource
                self.handle_resource(
                    embedded_resource, stack, dc_label, stack_update)
            except Exception as e:
                print('Could not create Router: ' + str(e))
            return

        LOG.warning(
            'Could not determine resource type: {}'.format(resource['type']))
        return

    def shorten_server_name(self, server_name, stack):
        """
        Shortens the server name to a maximum of 12 characters plus the iterator string, if the original name was
        used before.

        :param server_name: The original server name.
        :type server_name: ``str``
        :param stack: A reference to the used stack.
        :type stack: :class:`heat.resources.stack`
        :return: A string with max. 12 characters plus iterator string.
        :rtype: ``str``
        """
        server_name = self.shorten_name(server_name, 12)
        iterator = 0
        while server_name in stack.servers:
            server_name = server_name[0:12] + str(iterator)
            iterator += 1
        return server_name

    def shorten_name(self, name, max_size):
        """
        Shortens the name to max_size characters and replaces all '-' with '_'.

        :param name: The original string.
        :type name: ``str``
        :param max_size: The number of allowed characters.
        :type max_size: ``int``
        :return: String with at most max_size characters and without '-'.
        :rtype: ``str``
        """
        shortened_name = name.split(':', 1)[0]
        shortened_name = shortened_name.replace("-", "_")
        shortened_name = shortened_name[0:max_size]
        return shortened_name

    def check_template_version(self, version_string):
        """
        Checks if a version string is equal or later than 30-04-2015

        :param version_string: String with the version.
        :type version_string: ``str``
        :return: * *True*: if the version is equal or later 30-04-2015.
         * *False*: else
        :rtype: ``bool``
        """
        r = re.compile('\d{4}-\d{2}-\d{2}')
        if not r.match(version_string):
            return False

        year, month, day = map(int, version_string.split('-', 2))
        if year < 2015:
            return False
        if year == 2015:
            if month < 0o4:
                return False
            if month == 0o4 and day < 30:
                return False
        return True
