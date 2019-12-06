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
from mininet.link import Link

from emuvim.api.openstack.resources.instance_flavor import InstanceFlavor
from emuvim.api.openstack.resources.net import Net
from emuvim.api.openstack.resources.port import Port
from emuvim.api.openstack.resources.port_pair import PortPair
from emuvim.api.openstack.resources.port_pair_group import PortPairGroup
from emuvim.api.openstack.resources.flow_classifier import FlowClassifier
from emuvim.api.openstack.resources.port_chain import PortChain
from emuvim.api.openstack.resources.server import Server
from emuvim.api.openstack.resources.image import Image

from docker import DockerClient
import logging
import threading
import uuid
import time
import emuvim.api.openstack.ip_handler as IP
import hashlib


LOG = logging.getLogger("api.openstack.compute")


class HeatApiStackInvalidException(Exception):
    """
    Exception thrown when a submitted stack is invalid.
    """

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return repr(self.value)


class OpenstackCompute(object):
    """
    This class is a datacenter specific compute object that tracks all containers that are running in a datacenter,
    as well as networks and configured ports.
    It has some stack dependet logic and can check if a received stack is valid.

    It also handles start and stop of containers.
    """

    def __init__(self):
        self.dc = None
        self.stacks = dict()
        self.computeUnits = dict()
        self.routers = dict()
        self.flavors = dict()
        self._images = dict()
        self.nets = dict()
        self.ports = dict()
        self.port_pairs = dict()
        self.port_pair_groups = dict()
        self.flow_classifiers = dict()
        self.port_chains = dict()
        self.compute_nets = dict()
        self.dcli = DockerClient(base_url='unix://var/run/docker.sock')

    @property
    def images(self):
        """
        Updates the known images. Asks the docker daemon for a list of all known images and returns
        the new dictionary.

        :return: Returns the new image dictionary.
        :rtype: ``dict``
        """
        for image in self.dcli.images.list():
            if len(image.tags) > 0:
                for t in image.tags:
                    if t not in self._images:
                        self._images[t] = Image(t)
        return self._images

    def add_stack(self, stack):
        """
        Adds a new stack to the compute node.

        :param stack: Stack dictionary.
        :type stack: :class:`heat.resources.stack`
        """
        if not self.check_stack(stack):
            self.clean_broken_stack(stack)
            raise HeatApiStackInvalidException(
                "Stack did not pass validity checks")
        self.stacks[stack.id] = stack

    def clean_broken_stack(self, stack):
        for port in stack.ports.values():
            if port.id in self.ports:
                del self.ports[port.id]
        for server in stack.servers.values():
            if server.id in self.computeUnits:
                del self.computeUnits[server.id]
        for net in stack.nets.values():
            if net.id in self.nets:
                del self.nets[net.id]

    def check_stack(self, stack):
        """
        Checks all dependencies of all servers, ports and routers and their most important parameters.

        :param stack: A reference of the stack that should be checked.
        :type stack: :class:`heat.resources.stack`
        :return: * *True*: If the stack is completely fine.
         * *False*: Else
        :rtype: ``bool``
        """
        everything_ok = True
        for server in stack.servers.values():
            for port_name in server.port_names:
                if port_name not in stack.ports:
                    LOG.warning("Server %s of stack %s has a port named %s that is not known." %
                                (server.name, stack.stack_name, port_name))
                    everything_ok = False
            if server.image is None:
                LOG.warning("Server %s holds no image." % (server.name))
                everything_ok = False
            if server.command is None:
                LOG.warning("Server %s holds no command." % (server.name))
                everything_ok = False
        for port in stack.ports.values():
            if port.net_name not in stack.nets:
                LOG.warning("Port %s of stack %s has a network named %s that is not known." %
                            (port.name, stack.stack_name, port.net_name))
                everything_ok = False
            if port.intf_name is None:
                LOG.warning("Port %s has no interface name." % (port.name))
                everything_ok = False
            if port.ip_address is None:
                LOG.warning("Port %s has no IP address." % (port.name))
                everything_ok = False
        for router in stack.routers.values():
            for subnet_name in router.subnet_names:
                found = False
                for net in stack.nets.values():
                    if net.subnet_name == subnet_name:
                        found = True
                        break
                if not found:
                    LOG.warning("Router %s of stack %s has a network named %s that is not known." %
                                (router.name, stack.stack_name, subnet_name))
                    everything_ok = False
        return everything_ok

    def add_flavor(self, name, cpu, memory,
                   memory_unit, storage, storage_unit):
        """
        Adds a flavor to the stack.

        :param name: Specifies the name of the flavor.
        :type name: ``str``
        :param cpu:
        :type cpu: ``str``
        :param memory:
        :type memory: ``str``
        :param memory_unit:
        :type memory_unit: ``str``
        :param storage:
        :type storage: ``str``
        :param storage_unit:
        :type storage_unit: ``str``
        """
        flavor = InstanceFlavor(
            name, cpu, memory, memory_unit, storage, storage_unit)
        self.flavors[flavor.name] = flavor
        return flavor

    def deploy_stack(self, stackid):
        """
        Deploys the stack and starts the emulation.

        :param stackid: An UUID str of the stack
        :type stackid: ``str``
        :return: * *False*: If the Datacenter is None
            * *True*: Else
        :rtype: ``bool``
        """
        if self.dc is None:
            return False

        stack = self.stacks[stackid]
        self.update_compute_dicts(stack)

        # Create the networks first
        for server in stack.servers.values():
            self._start_compute(server)
        return True

    def delete_stack(self, stack_id):
        """
        Delete a stack and all its components.

        :param stack_id: An UUID str of the stack
        :type stack_id: ``str``
        :return: * *False*: If the Datacenter is None
            * *True*: Else
        :rtype: ``bool``
        """
        if self.dc is None:
            return False

        # Stop all servers and their links of this stack
        for server in self.stacks[stack_id].servers.values():
            self.stop_compute(server)
            self.delete_server(server)
        stack = list(self.stacks[stack_id].nets.values())
        while stack:
            id = stack.pop().id
            self.delete_network(id)
        # for net in self.stacks[stack_id].nets.values():
        # self.delete_network(net.id)
        for port in self.stacks[stack_id].ports.values():
            self.delete_port(port.id)

        del self.stacks[stack_id]
        return True

    def update_stack(self, old_stack_id, new_stack):
        """
        Determines differences within the old and the new stack and deletes, create or changes only parts that
        differ between the two stacks.

        :param old_stack_id: The ID of the old stack.
        :type old_stack_id: ``str``
        :param new_stack: A reference of the new stack.
        :type new_stack: :class:`heat.resources.stack`
        :return: * *True*: if the old stack could be updated to the new stack without any error.
            * *False*: else
        :rtype: ``bool``
        """
        LOG.debug("updating stack {} with new_stack {}".format(
            old_stack_id, new_stack))
        if old_stack_id not in self.stacks:
            return False
        old_stack = self.stacks[old_stack_id]

        # Update Stack IDs
        for server in old_stack.servers.values():
            if server.name in new_stack.servers:
                new_stack.servers[server.name].id = server.id
        for net in old_stack.nets.values():
            if net.name in new_stack.nets:
                new_stack.nets[net.name].id = net.id
                for subnet in new_stack.nets.values():
                    if subnet.subnet_name == net.subnet_name:
                        subnet.subnet_id = net.subnet_id
                        break
        for port in old_stack.ports.values():
            if port.name in new_stack.ports:
                new_stack.ports[port.name].id = port.id
        for router in old_stack.routers.values():
            if router.name in new_stack.routers:
                new_stack.routers[router.name].id = router.id

        # Update the compute dicts to now contain the new_stack components
        self.update_compute_dicts(new_stack)

        self.update_ip_addresses(old_stack, new_stack)

        # Update all interface names - after each port has the correct UUID!!
        for port in new_stack.ports.values():
            port.create_intf_name()

        if not self.check_stack(new_stack):
            return False

        # Remove unnecessary networks
        for net in old_stack.nets.values():
            if net.name not in new_stack.nets:
                self.delete_network(net.id)

        # Remove all unnecessary servers
        for server in old_stack.servers.values():
            if server.name in new_stack.servers:
                if not server.compare_attributes(
                        new_stack.servers[server.name]):
                    self.stop_compute(server)
                else:
                    # Delete unused and changed links
                    for port_name in server.port_names:
                        if port_name in old_stack.ports and port_name in new_stack.ports:
                            if not old_stack.ports.get(
                                    port_name) == new_stack.ports.get(port_name):
                                my_links = self.dc.net.links
                                for link in my_links:
                                    if str(link.intf1) == old_stack.ports[port_name].intf_name and \
                                            str(link.intf1.ip) == \
                                            old_stack.ports[port_name].ip_address.split('/')[0]:
                                        self._remove_link(server.name, link)

                                        # Add changed link
                                        self._add_link(server.name,
                                                       new_stack.ports[port_name].ip_address,
                                                       new_stack.ports[port_name].intf_name,
                                                       new_stack.ports[port_name].net_name)
                                        break
                        else:
                            my_links = self.dc.net.links
                            for link in my_links:
                                if str(link.intf1) == old_stack.ports[port_name].intf_name and \
                                   str(link.intf1.ip) == old_stack.ports[port_name].ip_address.split('/')[0]:
                                    self._remove_link(server.name, link)
                                    break

                    # Create new links
                    for port_name in new_stack.servers[server.name].port_names:
                        if port_name not in server.port_names:
                            self._add_link(server.name,
                                           new_stack.ports[port_name].ip_address,
                                           new_stack.ports[port_name].intf_name,
                                           new_stack.ports[port_name].net_name)
            else:
                self.stop_compute(server)

        # Start all new servers
        for server in new_stack.servers.values():
            if server.name not in self.dc.containers:
                self._start_compute(server)
            else:
                server.emulator_compute = self.dc.containers.get(server.name)

        del self.stacks[old_stack_id]
        self.stacks[new_stack.id] = new_stack
        return True

    def update_ip_addresses(self, old_stack, new_stack):
        """
        Updates the subnet and the port IP addresses - which should always be in this order!

        :param old_stack: The currently running stack
        :type old_stack: :class:`heat.resources.stack`
        :param new_stack: The new created stack
        :type new_stack: :class:`heat.resources.stack`
        """
        self.update_subnet_cidr(old_stack, new_stack)
        self.update_port_addresses(old_stack, new_stack)

    def update_port_addresses(self, old_stack, new_stack):
        """
        Updates the port IP addresses. First resets all issued addresses. Then get all IP addresses from the old
        stack and sets them to the same ports in the new stack. Finally all new or changed instances will get new
        IP addresses.

        :param old_stack: The currently running stack
        :type old_stack: :class:`heat.resources.stack`
        :param new_stack: The new created stack
        :type new_stack: :class:`heat.resources.stack`
        """
        for net in new_stack.nets.values():
            net.reset_issued_ip_addresses()

        for old_port in old_stack.ports.values():
            for port in new_stack.ports.values():
                if port.compare_attributes(old_port):
                    for net in new_stack.nets.values():
                        if net.name == port.net_name:
                            if net.assign_ip_address(
                                    old_port.ip_address, port.name):
                                port.ip_address = old_port.ip_address
                                port.mac_address = old_port.mac_address
                            else:
                                port.ip_address = net.get_new_ip_address(
                                    port.name)

        for port in new_stack.ports.values():
            for net in new_stack.nets.values():
                if port.net_name == net.name and not net.is_my_ip(
                        port.ip_address, port.name):
                    port.ip_address = net.get_new_ip_address(port.name)

    def update_subnet_cidr(self, old_stack, new_stack):
        """
        Updates the subnet IP addresses. If the new stack contains subnets from the old stack it will take those
        IP addresses. Otherwise it will create new IP addresses for the subnet.

        :param old_stack: The currently running stack
        :type old_stack: :class:`heat.resources.stack`
        :param new_stack: The new created stack
        :type new_stack: :class:`heat.resources.stack`
        """
        for old_subnet in old_stack.nets.values():
            IP.free_cidr(old_subnet.get_cidr(), old_subnet.subnet_id)

        for subnet in new_stack.nets.values():
            subnet.clear_cidr()
            for old_subnet in old_stack.nets.values():
                if subnet.subnet_name == old_subnet.subnet_name:
                    if IP.assign_cidr(old_subnet.get_cidr(), subnet.subnet_id):
                        subnet.set_cidr(old_subnet.get_cidr())

        for subnet in new_stack.nets.values():
            if IP.is_cidr_issued(subnet.get_cidr()):
                continue

            cird = IP.get_new_cidr(subnet.subnet_id)
            subnet.set_cidr(cird)
        return

    def update_compute_dicts(self, stack):
        """
        Update and add all stack components tho the compute dictionaries.

        :param stack: A stack reference, to get all required components.
        :type stack: :class:`heat.resources.stack`
        """
        for server in stack.servers.values():
            self.computeUnits[server.id] = server
            if isinstance(server.flavor, dict):
                self.add_flavor(server.flavor['flavorName'],
                                server.flavor['vcpu'],
                                server.flavor['ram'], 'MB',
                                server.flavor['storage'], 'GB')
                server.flavor = server.flavor['flavorName']
        for router in stack.routers.values():
            self.routers[router.id] = router
        for net in stack.nets.values():
            self.nets[net.id] = net
        for port in stack.ports.values():
            self.ports[port.id] = port

    def _start_compute(self, server):
        """
        Starts a new compute object (docker container) inside the emulator.
        Should only be called by stack modifications and not directly.

        :param server: Specifies the compute resource.
        :type server: :class:`heat.resources.server`
        """
        LOG.debug("Starting new compute resources %s" % server.name)
        network = list()
        network_dict = dict()

        for port_name in server.port_names:
            network_dict = dict()
            port = self.find_port_by_name_or_id(port_name)
            if port is not None:
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network_dict[network_dict['id']] = self.find_network_by_name_or_id(
                    port.net_name).name
                network.append(network_dict)
        # default network dict
        if len(network) < 1:
            network_dict['id'] = server.name + "-eth0"
            network_dict[network_dict['id']] = network_dict['id']
            network.append(network_dict)

        self.compute_nets[server.name] = network
        LOG.debug("Network dict: {}".format(network))
        c = self.dc.startCompute(server.name, image=server.image, command=server.command,
                                 network=network, flavor_name=server.flavor,
                                 properties=server.properties)
        server.emulator_compute = c

        for intf in c.intfs.values():
            for port_name in server.port_names:
                port = self.find_port_by_name_or_id(port_name)
                if port is not None:
                    if intf.name == port.intf_name:
                        # wait up to one second for the intf to come up
                        self.timeout_sleep(intf.isUp, 1)
                        if port.mac_address is not None:
                            intf.setMAC(port.mac_address)
                        else:
                            port.mac_address = intf.MAC()
                        port.assigned_container = c

        # Start the real emulator command now as specified in the dockerfile
        config = c.dcinfo.get("Config", dict())
        env = config.get("Env", list())
        legacy_command_execution = False
        for env_var in env:
            var, cmd = map(str.strip, map(str, env_var.split('=', 1)))
            if var == "SON_EMU_CMD" or var == "VIM_EMU_CMD":
                LOG.info("Executing script in '{}': {}={}"
                         .format(server.name, var, cmd))
                # execute command in new thread to ensure that GK is not
                # blocked by VNF
                t = threading.Thread(target=c.cmdPrint, args=(cmd,))
                t.daemon = True
                t.start()
                legacy_command_execution = True
                break  # only execute one command
        if not legacy_command_execution:
            c.start()

    def stop_compute(self, server):
        """
        Determines which links should be removed before removing the server itself.

        :param server: The server that should be removed
        :type server: ``heat.resources.server``
        """
        LOG.debug("Stopping container %s with full name %s" %
                  (server.name, server.full_name))
        link_names = list()
        for port_name in server.port_names:
            prt = self.find_port_by_name_or_id(port_name)
            if prt is not None:
                link_names.append(prt.intf_name)
        my_links = self.dc.net.links
        for link in my_links:
            if str(link.intf1) in link_names:
                # Remove all self created links that connect the server to the
                # main switch
                self._remove_link(server.name, link)

        # Stop the server and the remaining connection to the datacenter switch
        self.dc.stopCompute(server.name)
        # Only now delete all its ports and the server itself
        for port_name in server.port_names:
            self.delete_port(port_name)
        self.delete_server(server)

    def find_server_by_name_or_id(self, name_or_id):
        """
        Tries to find the server by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the server.
        :type name_or_id: ``str``
        :return: Returns the server reference if it was found or None
        :rtype: :class:`heat.resources.server`
        """
        if name_or_id in self.computeUnits:
            return self.computeUnits[name_or_id]

        if self._shorten_server_name(name_or_id) in self.computeUnits:
            return self.computeUnits[name_or_id]

        for server in self.computeUnits.values():
            if (server.name == name_or_id or
                    server.template_name == name_or_id or
                    server.full_name == name_or_id):
                return server
            if (server.name == self._shorten_server_name(name_or_id) or
                    server.template_name == self._shorten_server_name(name_or_id) or
                    server.full_name == self._shorten_server_name(name_or_id)):
                return server
        return None

    def create_server(self, name, stack_operation=False):
        """
        Creates a server with the specified name. Raises an exception when a server with the given name already
        exists!

        :param name: Name of the new server.
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: Returns the created server.
        :rtype: :class:`heat.resources.server`
        """
        if self.find_server_by_name_or_id(
                name) is not None and not stack_operation:
            raise Exception("Server with name %s already exists." % name)
        safe_name = self._shorten_server_name(name)
        server = Server(safe_name)
        server.id = str(uuid.uuid4())
        if not stack_operation:
            self.computeUnits[server.id] = server
        return server

    def _shorten_server_name(self, name, char_limit=9):
        """
        Docker does not like too long instance names.
        This function provides a shorter name if needed
        """
        if len(name) > char_limit:
            # construct a short name
            h = hashlib.sha224(name.encode()).hexdigest()
            h = h[0:char_limit]
            LOG.debug("Shortened server name '%s' to '%s'" % (name, h))
        return name

    def delete_server(self, server):
        """
        Deletes the given server from the stack dictionary and the computeUnits dictionary.

        :param server: Reference of the server that should be deleted.
        :type server: :class:`heat.resources.server`
        :return: * *False*: If the server name is not in the correct format ('datacentername_stackname_servername') \
                or when no stack with the correct stackname was found.
            * *True*: Else
        :rtype: ``bool``
        """
        if server is None:
            return False
        name_parts = server.name.split('_')
        if len(name_parts) > 1:
            for stack in self.stacks.values():
                if stack.stack_name == name_parts[1]:
                    stack.servers.pop(server.id, None)
        if self.computeUnits.pop(server.id, None) is None:
            return False
        return True

    def find_network_by_name_or_id(self, name_or_id):
        """
        Tries to find the network by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the network.
        :type name_or_id: ``str``
        :return: Returns the network reference if it was found or None
        :rtype: :class:`heat.resources.net`
        """
        if name_or_id in self.nets:
            return self.nets[name_or_id]
        print("name_or_id: ", name_or_id)
        for net in self.nets.values():
            if net.name == name_or_id:
                return net
        LOG.warning("Could not find net '{}' in {} or {}"
                    .format(name_or_id,
                            self.nets.keys(),
                            [n.name for n in self.nets.values()]))
        return None

    def create_network(self, name, stack_operation=False):
        """
        Creates a new network with the given name. Raises an exception when a network with the given name already
        exists!

        :param name: Name of the new network.
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: :class:`heat.resources.net`
        """
        LOG.debug("Creating network with name %s" % name)
        if self.find_network_by_name_or_id(
                name) is not None and not stack_operation:
            LOG.warning(
                "Creating network with name %s failed, as it already exists" % name)
            raise Exception("Network with name %s already exists." % name)
        network = Net(name)
        network.id = str(uuid.uuid4())
        if not stack_operation:
            self.nets[network.id] = network
        return network

    def delete_network(self, name_or_id):
        """
        Deletes the given network.

        :param name_or_id: Name or UUID of the network.
        :type name_or_id: ``str``
        """
        net = self.find_network_by_name_or_id(name_or_id)
        if net is None:
            raise Exception(
                "Network with name or id %s does not exists." % name_or_id)

        for stack in self.stacks.values():
            stack.nets.pop(net.name, None)

        self.nets.pop(net.id, None)

    def create_port(self, name, stack_operation=False):
        """
        Creates a new port with the given name. Raises an exception when a port with the given name already
        exists!

        :param name: Name of the new port.
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: Returns the created port.
        :rtype: :class:`heat.resources.port`
        """
        port = Port(name)
        if not stack_operation:
            self.ports[port.id] = port
            port.create_intf_name()
        return port

    def find_port_by_name_or_id(self, name_or_id):
        """
        Tries to find the port by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the network.
        :type name_or_id: ``str``
        :return: Returns the port reference if it was found or None
        :rtype: :class:`heat.resources.port`
        """
        # find by id
        if name_or_id in self.ports:
            return self.ports[name_or_id]
        # find by name
        matching_ports = list(filter(
            lambda port: port.name == name_or_id or port.template_name == name_or_id,
            self.ports.values()
        ))
        matching_ports_count = len(matching_ports)
        if matching_ports_count == 1:
            return matching_ports[0]
        if matching_ports_count > 1:
            raise RuntimeError("Ambiguous port name %s" % name_or_id)
        return None

    def delete_port(self, name_or_id):
        """
        Deletes the given port. Raises an exception when the port was not found!

        :param name_or_id:  UUID or name of the port.
        :type name_or_id: ``str``
        """
        port = self.find_port_by_name_or_id(name_or_id)
        if port is None:
            LOG.warning(
                "Port with name or id %s does not exist. Can't delete it." % name_or_id)
            return

        my_links = self.dc.net.links
        for link in my_links:
            if str(link.intf1) == port.intf_name:
                self._remove_link(link.intf1.node.name, link)
                break

        self.ports.pop(port.id, None)
        for stack in self.stacks.values():
            stack.ports.pop(port.name, None)

    def create_port_pair(self, name, stack_operation=False):
        """
        Creates a new port pair with the given name. Raises an exception when a port pair with the given name already
        exists!

        :param name: Name of the new port pair.
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: Returns the created port pair.
        :rtype: :class:`openstack.resources.port_pair`
        """
        port_pair = self.find_port_pair_by_name_or_id(name)
        if port_pair is not None and not stack_operation:
            logging.warning(
                "Creating port pair with name %s failed, as it already exists" % name)
            raise Exception("Port pair with name %s already exists." % name)
        logging.debug("Creating port pair with name %s" % name)
        port_pair = PortPair(name)
        if not stack_operation:
            self.port_pairs[port_pair.id] = port_pair
        return port_pair

    def find_port_pair_by_name_or_id(self, name_or_id):
        """
        Tries to find the port pair by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the port pair.
        :type name_or_id: ``str``
        :return: Returns the port pair reference if it was found or None
        :rtype: :class:`openstack.resources.port_pair`
        """
        if name_or_id in self.port_pairs:
            return self.port_pairs[name_or_id]
        for port_pair in self.port_pairs.values():
            if port_pair.name == name_or_id:
                return port_pair

        return None

    def delete_port_pair(self, name_or_id):
        """
        Deletes the given port pair. Raises an exception when the port pair was not found!

        :param name_or_id:  UUID or name of the port pair.
        :type name_or_id: ``str``
        """
        port_pair = self.find_port_pair_by_name_or_id(name_or_id)
        if port_pair is None:
            raise Exception(
                "Port pair with name or id %s does not exists." % name_or_id)

        self.port_pairs.pop(port_pair.id, None)

    def create_port_pair_group(self, name, stack_operation=False):
        """
        Creates a new port pair group with the given name. Raises an exception when a port pair group
        with the given name already exists!

        :param name: Name of the new port pair group.
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: Returns the created port pair group .
        :rtype: :class:`openstack.resources.port_pair_group`
        """
        port_pair_group = self.find_port_pair_group_by_name_or_id(name)
        if port_pair_group is not None and not stack_operation:
            logging.warning(
                "Creating port pair group with name %s failed, as it already exists" % name)
            raise Exception(
                "Port pair group with name %s already exists." % name)
        logging.debug("Creating port pair group with name %s" % name)
        port_pair_group = PortPairGroup(name)
        if not stack_operation:
            self.port_pair_groups[port_pair_group.id] = port_pair_group
        return port_pair_group

    def find_port_pair_group_by_name_or_id(self, name_or_id):
        """
        Tries to find the port pair group by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the port pair group.
        :type name_or_id: ``str``
        :return: Returns the port pair group reference if it was found or None
        :rtype: :class:`openstack.resources.port_pair_group`
        """
        if name_or_id in self.port_pair_groups:
            return self.port_pair_groups[name_or_id]
        for port_pair_group in self.port_pair_groups.values():
            if port_pair_group.name == name_or_id:
                return port_pair_group

        return None

    def delete_port_pair_group(self, name_or_id):
        """
        Deletes the given port pair group. Raises an exception when the port pair group was not found!

        :param name_or_id:  UUID or name of the port pair group.
        :type name_or_id: ``str``
        """
        port_pair_group = self.find_port_pair_group_by_name_or_id(name_or_id)
        if port_pair_group is None:
            raise Exception(
                "Port pair with name or id %s does not exists." % name_or_id)

        self.port_pair_groups.pop(port_pair_group.id, None)

    def create_port_chain(self, name, stack_operation=False):
        """
        Creates a new port chain with the given name. Raises an exception when a port chain with the given name already
        exists!

        :param name: Name of the new port chain
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: Returns the created port chain.
        :rtype: :class:`openstack.resources.port_chain.PortChain`
        """
        port_chain = self.find_port_chain_by_name_or_id(name)
        if port_chain is not None and not stack_operation:
            logging.warning(
                "Creating port chain with name %s failed, as it already exists" % name)
            raise Exception("Port chain with name %s already exists." % name)
        logging.debug("Creating port chain with name %s" % name)
        port_chain = PortChain(name)
        if not stack_operation:
            self.port_chains[port_chain.id] = port_chain
        return port_chain

    def find_port_chain_by_name_or_id(self, name_or_id):
        """
        Tries to find the port chain by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the port chain.
        :type name_or_id: ``str``
        :return: Returns the port chain reference if it was found or None
        :rtype: :class:`openstack.resources.port_chain.PortChain`
        """
        if name_or_id in self.port_chains:
            return self.port_chains[name_or_id]
        for port_chain in self.port_chains.values():
            if port_chain.name == name_or_id:
                return port_chain
        return None

    def delete_port_chain(self, name_or_id):
        """
        Deletes the given port chain. Raises an exception when the port chain was not found!

        :param name_or_id:  UUID or name of the port chain.
        :type name_or_id: ``str``
        """
        port_chain = self.find_port_chain_by_name_or_id(name_or_id)
        port_chain.uninstall(self)
        if port_chain is None:
            raise Exception(
                "Port chain with name or id %s does not exists." % name_or_id)

        self.port_chains.pop(port_chain.id, None)

    def create_flow_classifier(self, name, stack_operation=False):
        """
        Creates a new flow classifier with the given name. Raises an exception when a flow classifier with the given name already
        exists!

        :param name: Name of the new flow classifier.
        :type name: ``str``
        :param stack_operation: Allows the heat parser to create modules without adapting the current emulation.
        :type stack_operation: ``bool``
        :return: Returns the created flow classifier.
        :rtype: :class:`openstack.resources.flow_classifier`
        """
        flow_classifier = self.find_flow_classifier_by_name_or_id(name)
        if flow_classifier is not None and not stack_operation:
            logging.warning(
                "Creating flow classifier with name %s failed, as it already exists" % name)
            raise Exception(
                "Flow classifier with name %s already exists." % name)
        logging.debug("Creating flow classifier with name %s" % name)
        flow_classifier = FlowClassifier(name)
        if not stack_operation:
            self.flow_classifiers[flow_classifier.id] = flow_classifier
        return flow_classifier

    def find_flow_classifier_by_name_or_id(self, name_or_id):
        """
        Tries to find the flow classifier by ID and if this does not succeed then tries to find it via name.

        :param name_or_id: UUID or name of the flow classifier.
        :type name_or_id: ``str``
        :return: Returns the flow classifier reference if it was found or None
        :rtype: :class:`openstack.resources.flow_classifier`
        """
        if name_or_id in self.flow_classifiers:
            return self.flow_classifiers[name_or_id]
        for flow_classifier in self.flow_classifiers.values():
            if flow_classifier.name == name_or_id:
                return flow_classifier

        return None

    def delete_flow_classifier(self, name_or_id):
        """
        Deletes the given flow classifier. Raises an exception when the flow classifier was not found!

        :param name_or_id:  UUID or name of the flow classifier.
        :type name_or_id: ``str``
        """
        flow_classifier = self.find_flow_classifier_by_name_or_id(name_or_id)
        if flow_classifier is None:
            raise Exception(
                "Flow classifier with name or id %s does not exists." % name_or_id)

        self.flow_classifiers.pop(flow_classifier.id, None)

    def _add_link(self, node_name, ip_address, link_name, net_name):
        """
        Adds a new link between datacenter switch and the node with the given name.

        :param node_name: Name of the required node.
        :type node_name: ``str``
        :param ip_address: IP-Address of the node.
        :type ip_address: ``str``
        :param link_name: Link name.
        :type link_name: ``str``
        :param net_name: Network name.
        :type net_name: ``str``
        """
        node = self.dc.net.get(node_name)
        params = {'params1': {'ip': ip_address,
                              'id': link_name,
                              link_name: net_name},
                  'intfName1': link_name,
                  'cls': Link}
        link = self.dc.net.addLink(node, self.dc.switch, **params)
        OpenstackCompute.timeout_sleep(link.intf1.isUp, 1)

    def _remove_link(self, server_name, link):
        """
        Removes a link between server and datacenter switch.

        :param server_name: Specifies the server where the link starts.
        :type server_name: ``str``
        :param link: A reference of the link which should be removed.
        :type link: :class:`mininet.link`
        """
        self.dc.switch.detach(link.intf2)
        del self.dc.switch.intfs[self.dc.switch.ports[link.intf2]]
        del self.dc.switch.ports[link.intf2]
        del self.dc.switch.nameToIntf[link.intf2.name]
        self.dc.net.removeLink(link=link)
        for intf_key in self.dc.net[server_name].intfs.keys():
            if self.dc.net[server_name].intfs[intf_key].link == link:
                self.dc.net[server_name].intfs[intf_key].delete()
                del self.dc.net[server_name].intfs[intf_key]

    @staticmethod
    def timeout_sleep(function, max_sleep):
        """
        This function will execute a function all 0.1 seconds until it successfully returns.
        Will return after `max_sleep` seconds if not successful.

        :param function: The function to execute. Should return true if done.
        :type function: ``function``
        :param max_sleep: Max seconds to sleep. 1 equals 1 second.
        :type max_sleep: ``float``
        """
        current_time = time.time()
        stop_time = current_time + max_sleep
        while not function() and current_time < stop_time:
            current_time = time.time()
            time.sleep(0.1)
