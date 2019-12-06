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
from flask import Flask, send_from_directory
from flask_restful import Api
from gevent.pywsgi import WSGIServer

# need to import total module to set its global variable dcs
from emuvim.api.rest import compute
from emuvim.api.rest.compute import ComputeList, Compute, ComputeResources, DatacenterList, DatacenterStatus

# need to import total module to set its global variable net
from emuvim.api.rest import network
from emuvim.api.rest.network import NetworkAction, DrawD3jsgraph

from emuvim.api.rest import monitor
from emuvim.api.rest.monitor import MonitorInterfaceAction, MonitorFlowAction, MonitorLinkAction, MonitorSkewAction, MonitorTerminal

import pkg_resources
from os import path


logging.basicConfig()


class RestApiEndpoint(object):
    """
    Simple API endpoint that offers a REST
    interface. This interface will be used by the
    default command line client.
    """

    def __init__(self, listenip, port, DCnetwork=None):
        self.ip = listenip
        self.port = port

        # connect this DC network to the rest api endpoint (needed for the
        # networking and monitoring api)
        self.connectDCNetwork(DCnetwork)

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

        # define dashboard endpoints
        db_dir, db_file = self.get_dashboard_path()

        @self.app.route('/dashboard/<path:path>')
        def db_file(path):
            logging.info("[DB] Serving: {}".format(path))
            return send_from_directory(db_dir, path)

        # define REST API endpoints
        # compute related actions (start/stop VNFs, get info)
        self.api.add_resource(
            Compute, "/restapi/compute/<dc_label>/<compute_name>")
        self.api.add_resource(ComputeList,
                              "/restapi/compute",
                              "/restapi/compute/<dc_label>")
        self.api.add_resource(
            ComputeResources, "/restapi/compute/resources/<dc_label>/<compute_name>")

        self.api.add_resource(
            DatacenterStatus, "/restapi/datacenter/<dc_label>")
        self.api.add_resource(DatacenterList, "/restapi/datacenter")

        # network related actions (setup chaining between VNFs)
        self.api.add_resource(NetworkAction,
                              "/restapi/network")
        self.api.add_resource(DrawD3jsgraph,
                              "/restapi/network/d3jsgraph")

        # monitoring related actions
        # export a network interface traffic rate counter
        self.api.add_resource(MonitorInterfaceAction,
                              "/restapi/monitor/interface")
        # export flow traffic counter, of a manually pre-installed flow entry,
        # specified by its cookie
        self.api.add_resource(MonitorFlowAction,
                              "/restapi/monitor/flow")
        # install monitoring of a specific flow on a pre-existing link in the service.
        # the traffic counters of the newly installed monitor flow are exported
        self.api.add_resource(MonitorLinkAction,
                              "/restapi/monitor/link")
        # install skewness monitor of resource usage disribution
        # the skewness metric is exported
        self.api.add_resource(MonitorSkewAction,
                              "/restapi/monitor/skewness")
        # start a terminal window for the specified vnfs
        self.api.add_resource(MonitorTerminal,
                              "/restapi/monitor/term")

        logging.debug("Created API endpoint %s(%s:%d)" %
                      (self.__class__.__name__, self.ip, self.port))

    def get_dashboard_path(self):
        """
        Return absolute path to dashboard files.
        """
        db_file = pkg_resources.resource_filename(
            'emuvim.dashboard', "index.html")
        db_dir = path.dirname(db_file)
        logging.info("[DB] Serving emulator dashboard from: {} and {}"
                     .format(db_dir, db_file))
        return db_dir, db_file

    def connectDatacenter(self, dc):
        compute.dcs[dc.label] = dc
        logging.info(
            "Connected DC(%s) to API endpoint %s(%s:%d)" % (dc.label, self.__class__.__name__, self.ip, self.port))

    def connectDCNetwork(self, DCnetwork):
        network.net = DCnetwork
        monitor.net = DCnetwork

        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):
        self.thread = threading.Thread(target=self._start_flask, args=())
        self.thread.daemon = True
        self.thread.start()
        logging.info("Started API endpoint @ http://%s:%d" %
                     (self.ip, self.port))

    def stop(self):
        if self.http_server:
            self.http_server.close()

    def _start_flask(self):
        # self.app.run(self.ip, self.port, debug=False, use_reloader=False)
        # this should be a more production-fit http-server
        # self.app.logger.setLevel(logging.ERROR)
        self.http_server = WSGIServer((self.ip, self.port),
                                      self.app,
                                      # This disables HTTP request logs to not
                                      # mess up the CLI when e.g. the
                                      # auto-updated dashboard is used
                                      log=open("/dev/null", "w")
                                      )
        self.http_server.serve_forever()
