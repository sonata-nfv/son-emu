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
import uuid


class Stack:
    def __init__(self, id=None):
        self.servers = dict()
        self.nets = dict()
        self.ports = dict()
        self.routers = dict()
        self.stack_name = None
        self.creation_time = None
        self.update_time = None
        self.status = None
        self.template = None
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

    def add_server(self, server):
        """
        Adds one server to the server dictionary.

        :param server: The server to add.
        :type server: :class:`heat.resources.server`
        """
        self.servers[server.name] = server

    def add_net(self, net):
        """
        Adds one network to the network dictionary.

        :param net: Network to add.
        :type net: :class:`heat.resources.net`
        """
        self.nets[net.name] = net

    def add_port(self, port):
        """
        Adds one port to the port dictionary.

        :param port: Port to add.
        :type port: :class:`heat.resources.port`
        """
        self.ports[port.name] = port

    def add_router(self, router):
        """
        Adds one router to the port dictionary.

        :param router: Router to add.
        :type router: :class:`heat.resources.router`
        """
        self.routers[router.name] = router
