"""
Copyright (c) 2017 SONATA-NFV and Paderborn University
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

Neither the name of the SONATA-NFV, Paderborn University
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
from flask import Flask, request
from flask_restful import Api, Resource
import logging

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
        self.playbook_file = '/tmp/son-emu-requests.log'
        with open(self.playbook_file, 'w'):
            pass

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

    def _start_flask(self):
        LOG.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        if self.app is not None:
            self.app.before_request(self.dump_playbook)
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

    def dump_playbook(self):
        with self.manage.lock:
            with open(self.playbook_file, 'a') as logfile:
                if len(request.data) > 0:
                    data = "# %s API\n" % str(self.__class__).split('.')[-1].rstrip('\'>')
                    data += "curl -X {type} -H \"Content-type: application/json\" -d '{data}' {url}".format(type=request.method,
                                                                                            data=request.data,
                                                                                            url=request.url)
                    logfile.write(data + "\n")
