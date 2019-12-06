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
import re
from json import dumps


class Net:
    def __init__(self, name):
        self.name = name
        self.id = None
        self.subnet_name = None
        self.subnet_id = None
        self.subnet_creation_time = None
        self.subnet_update_time = None
        self.gateway_ip = None
        self.segmentation_id = None  # not set
        self._cidr = None
        self.start_end_dict = None
        self._issued_ip_addresses = dict()

    def get_short_id(self):
        """
        Returns a shortened UUID, with only the first 6 characters.

        :return: First 6 characters of the UUID
        :rtype: ``str``
        """
        return str(self.id)[:6]

    def get_new_ip_address(self, port_name):
        """
        Calculates the next unused IP Address which belongs to the subnet.

        :param port_name: Specifies the port.
        :type port_name: ``str``
        :return: Returns a unused IP Address or none if all are in use.
        :rtype: ``str``
        """
        if self.start_end_dict is None:
            return None

        # First address as network address not usable
        int_start_ip = Net.ip_2_int(self.start_end_dict['start']) + 2
        # Second one is for gateways only
        # Last address for broadcasts
        int_end_ip = Net.ip_2_int(self.start_end_dict['end']) - 1
        while int_start_ip in self._issued_ip_addresses and int_start_ip <= int_end_ip:
            int_start_ip += 1

        if int_start_ip > int_end_ip:
            return None

        self._issued_ip_addresses[int_start_ip] = port_name
        return Net.int_2_ip(int_start_ip) + '/' + self._cidr.rsplit('/', 1)[1]

    def assign_ip_address(self, cidr, port_name):
        """
        Assigns the IP address to the port if it is currently NOT used.

        :param cidr: The cidr used by the port - e.g. 10.0.0.1/24
        :type cidr: ``str``
        :param port_name: The port name
        :type port_name: ``str``
        :return: * *False*: If the IP address is already issued or if it is not within this subnet mask.
            * *True*: Else
        """
        int_ip = Net.cidr_2_int(cidr)
        if int_ip in self._issued_ip_addresses:
            return False

        # First address as network address not usable
        int_start_ip = Net.ip_2_int(self.start_end_dict['start']) + 1
        # Last address for broadcasts
        int_end_ip = Net.ip_2_int(self.start_end_dict['end']) - 1
        if int_ip < int_start_ip or int_ip > int_end_ip:
            return False

        self._issued_ip_addresses[int_ip] = port_name
        return True

    def is_my_ip(self, cidr, port_name):
        """
        Checks if the IP is registered for this port name.

        :param cidr: The cidr used by the port - e.g. 10.0.0.1/24
        :type cidr: ``str``
        :param port_name: The port name
        :type port_name: ``str``
        :return: Returns true if the IP address belongs to the port name. Else it returns false.
        """
        int_ip = Net.cidr_2_int(cidr)

        if int_ip not in self._issued_ip_addresses:
            return False

        if self._issued_ip_addresses[int_ip] == port_name:
            return True
        return False

    def withdraw_ip_address(self, ip_address):
        """
        Removes the IP address from the list of issued addresses, thus other ports can use it.

        :param ip_address: The issued IP address.
        :type ip_address: ``str``
        """
        if ip_address is None:
            return

        if "/" in ip_address:
            address, suffix = ip_address.rsplit('/', 1)
        else:
            address = ip_address
        int_ip_address = Net.ip_2_int(address)
        if int_ip_address in self._issued_ip_addresses.keys():
            del self._issued_ip_addresses[int_ip_address]

    def reset_issued_ip_addresses(self):
        """
        Resets all issued IP addresses.
        """
        self._issued_ip_addresses = dict()

    def update_port_name_for_ip_address(self, ip_address, port_name):
        """
        Updates the port name of the issued IP address.

        :param ip_address: The already issued IP address.
        :type ip_address: ``str``
        :param port_name: The new port name
        :type port_name: ``str``
        """
        address, suffix = ip_address.rsplit('/', 1)
        int_ip_address = Net.ip_2_int(address)
        self._issued_ip_addresses[int_ip_address] = port_name

    def set_cidr(self, cidr):
        """
        Sets the CIDR for the subnet. It previously checks for the correct CIDR format.

        :param cidr: The new CIDR for the subnet.
        :type cidr: ``str``
        :return: * *True*: When the new CIDR was set successfully.
            * *False*: If the CIDR format was wrong.
        :rtype: ``bool``
        """
        if cidr is None:
            if self._cidr is not None:
                import emuvim.api.openstack.ip_handler as IP
                IP.free_cidr(self._cidr, self.subnet_id)
            self._cidr = None
            self.reset_issued_ip_addresses()
            self.start_end_dict = dict()
            return True
        if not Net.check_cidr_format(cidr):
            return False

        self.reset_issued_ip_addresses()
        self.start_end_dict = Net.calculate_start_and_end_dict(cidr)
        self._cidr = cidr
        return True

    def get_cidr(self):
        """
        Gets the CIDR.

        :return: The CIDR
        :rtype: ``str``
        """
        return self._cidr

    def clear_cidr(self):
        self._cidr = None
        self.start_end_dict = dict()
        self.reset_issued_ip_addresses()

    def delete_subnet(self):
        self.subnet_id = None
        self.subnet_name = None
        self.subnet_creation_time = None
        self.subnet_update_time = None
        self.set_cidr(None)

    @staticmethod
    def calculate_start_and_end_dict(cidr):
        """
        Calculates the start and end IP address for the subnet.

        :param cidr: The CIDR for the subnet.
        :type cidr: ``str``
        :return: Dict with start and end ip address
        :rtype: ``dict``
        """
        address, suffix = cidr.rsplit('/', 1)
        int_suffix = int(suffix)
        int_address = Net.ip_2_int(address)
        address_space = 2 ** 32 - 1

        for x in range(0, 31 - int_suffix):
            address_space = ~(~address_space | (1 << x))

        start = int_address & address_space
        end = start + (2 ** (32 - int_suffix) - 1)

        return {'start': Net.int_2_ip(start), 'end': Net.int_2_ip(end)}

    @staticmethod
    def cidr_2_int(cidr):
        if cidr is None:
            return None
        ip = cidr.rsplit('/', 1)[0]
        return Net.ip_2_int(ip)

    @staticmethod
    def ip_2_int(ip):
        """
        Converts a IP address to int.

        :param ip: IP address
        :type ip: ``str``
        :return: IP address as int.
        :rtype: ``int``
        """
        o = list(map(int, ip.split('.')))
        res = (16777216 * o[0]) + (65536 * o[1]) + (256 * o[2]) + o[3]
        return res

    @staticmethod
    def int_2_ip(int_ip):
        """
        Converts a int IP address to string.

        :param int_ip: Int IP address.
        :type int_ip: ``int``
        :return: IP address
        :rtype: ``str``
        """
        o1 = int(int_ip / 16777216) % 256
        o2 = int(int_ip / 65536) % 256
        o3 = int(int_ip / 256) % 256
        o4 = int(int_ip) % 256
        return '%(o1)s.%(o2)s.%(o3)s.%(o4)s' % locals()

    @staticmethod
    def check_cidr_format(cidr):
        """
        Checks the CIDR format. An valid example is: 192.168.0.0/29

        :param cidr: CIDR to be checked.
        :type cidr: ``str``
        :return: * *True*: If the Format is correct.
            * *False*: If it is not correct.
        :rtype: ``bool``
        """
        r = re.compile('\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}/\d{2}')
        if r.match(cidr):
            return True
        return False

    def create_network_dict(self):
        """
        Creates the network description dictionary.

        :return: Network description.
        :rtype: ``dict``
        """
        network_dict = dict()
        # TODO do we support inactive networks?
        network_dict["status"] = "ACTIVE"
        if self.subnet_id is None:
            network_dict["subnets"] = []
        else:
            network_dict["subnets"] = [self.subnet_id]
        network_dict["name"] = self.name
        network_dict["admin_state_up"] = True  # TODO is it always true?
        # TODO what should go in here
        network_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"
        network_dict["id"] = self.id
        network_dict["shared"] = False  # TODO is it always false?
        return network_dict

    def create_subnet_dict(self):
        """
        Creates the subnet description dictionary.

        :return: Subnet description.
        :rtype: ``dict``
        """
        subnet_dict = dict()
        subnet_dict["name"] = self.subnet_name
        subnet_dict["network_id"] = self.id
        # TODO what should go in here?
        subnet_dict["tenant_id"] = "abcdefghijklmnopqrstuvwxyz123456"
        subnet_dict["created_at"] = self.subnet_creation_time
        subnet_dict["dns_nameservers"] = []
        subnet_dict["allocation_pools"] = [self.start_end_dict]
        subnet_dict["host_routers"] = []
        subnet_dict["gateway_ip"] = self.gateway_ip
        subnet_dict["ip_version"] = "4"
        subnet_dict["cidr"] = self.get_cidr()
        subnet_dict["updated_at"] = self.subnet_update_time
        subnet_dict["id"] = self.subnet_id
        subnet_dict["enable_dhcp"] = False  # TODO do we support DHCP?
        return subnet_dict

    def __eq__(self, other):
        if self.name == other.name and self.subnet_name == other.subnet_name and \
                self.gateway_ip == other.gateway_ip and \
                self.segmentation_id == other.segmentation_id and \
                self._cidr == other._cidr and \
                self.start_end_dict == other.start_end_dict:
            return True
        return False

    def __hash__(self):
        return hash((self.name,
                     self.subnet_name,
                     self.gateway_ip,
                     self.segmentation_id,
                     self._cidr,
                     dumps(self.start_end_dict)))
