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

import threading
from flask import Flask, request
from flask_restful import Api, Resource
from gevent.pywsgi import WSGIServer


LOG = logging.getLogger("api.openstack.base")


class BaseOpenstackDummy(Resource):
    """
    This class is the base class for all openstack entrypoints of son-emu.
    """

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.compute = None
        self.manage = None
        self.http_server = None
        self.server_thread = None
        self.playbook_file = '/tmp/son-emu-requests.log'
        with open(self.playbook_file, 'w'):
            pass

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

    def start(self):
        self.server_thread = threading.Thread(target=self._start_flask, args=())
        self.server_thread.name = self.__class__.__name__
        self.server_thread.start()

    def stop(self):
        if self.http_server:
            LOG.info('Stopping %s' % self.__class__.__name__)
            self.http_server.stop(timeout=1)

    def _start_flask(self):
        LOG.info("Starting %s endpoint @ http://%s:%d" % (
            self.__class__.__name__, self.ip, self.port))
        self.http_server = WSGIServer(
            (self.ip, self.port),
            self.app,
            log=open("/dev/null", "w")  # don't show http logs
        )
        self.http_server.serve_forever(stop_timeout=1)
        LOG.info('Stopped %s' % self.__class__.__name__)

    def dump_playbook(self):
        with self.manage.lock:
            with open(self.playbook_file, 'a') as logfile:
                if len(request.data) > 0:
                    data = "# %s API\n" % str(
                        self.__class__).split('.')[-1].rstrip('\'>')
                    data += "curl -X {type} -H \"Content-type: application/json\" -d '{data}' {url}".format(type=request.method,
                                                                                                            data=request.data,
                                                                                                            url=request.url)
                    logfile.write(data + "\n")
