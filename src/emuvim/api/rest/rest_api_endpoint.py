"""
Copyright (c) 2015 SONATA-NFV and Paderborn University
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

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
import logging
import threading
from flask import Flask
from flask_restful import Api

# need to import total module to set its global variable dcs
import compute
from compute import dcs, ComputeList, Compute, DatacenterList, DatacenterStatus

# need to import total module to set its global variable net
import network
from network import NetworkAction

import monitor
from monitor import MonitorInterfaceAction, MonitorFlowAction, MonitorLinkAction, MonitorSkewAction

logging.basicConfig(level=logging.INFO)


class RestApiEndpoint(object):
    """
    Simple API endpoint that offers a REST
    interface. This interface will be used by the
    default command line client.
    """

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

        # setup endpoints

        # compute related actions (start/stop VNFs, get info)
        self.api.add_resource(Compute,
                              "/restapi/compute/<dc_label>/<compute_name>",
                              "/restapi/compute/<dc_label>/<compute_name>/<resource>/<value>")
        self.api.add_resource(ComputeList,
                      "/restapi/compute",
                      "/restapi/compute/<dc_label>")

        self.api.add_resource(DatacenterStatus, "/restapi/datacenter/<dc_label>")
        self.api.add_resource(DatacenterList, "/restapi/datacenter")


        # network related actions (setup chaining between VNFs)
        self.api.add_resource(NetworkAction,
                              "/restapi/network/<vnf_src_name>/<vnf_dst_name>")


        # monitoring related actions
        # export a network interface traffic rate counter
        self.api.add_resource(MonitorInterfaceAction,
                              "/restapi/monitor/interface/<vnf_name>/<metric>",
                              "/restapi/monitor/interface/<vnf_name>/<vnf_interface>/<metric>",
                              "/restapi/monitor/interface/<vnf_name>/<vnf_interface>/<metric>/<cookie>")
        # export flow traffic counter, of a manually pre-installed flow entry, specified by its cookie
        self.api.add_resource(MonitorFlowAction,
                              "/restapi/monitor/flow/<vnf_name>/<metric>/<cookie>",
                              "/restapi/monitor/flow/<vnf_name>/<vnf_interface>/<metric>/<cookie>")
        # install monitoring of a specific flow on a pre-existing link in the service.
        # the traffic counters of the newly installed monitor flow are exported
        self.api.add_resource(MonitorLinkAction,
                              "/restapi/monitor/link/<vnf_src_name>/<vnf_dst_name>")
        # install skewness monitor of resource usage disribution
        # the skewness metric is exported
        self.api.add_resource(MonitorSkewAction,
                              "/restapi/monitor/skewness/<vnf_name>/<resource_name>")

        logging.debug("Created API endpoint %s(%s:%d)" % (self.__class__.__name__, self.ip, self.port))

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
        thread = threading.Thread(target=self._start_flask, args=())
        thread.daemon = True
        thread.start()
        logging.info("Started API endpoint @ http://%s:%d" % (self.ip, self.port))

    def _start_flask(self):
        self.app.run(self.ip, self.port, debug=True, use_reloader=False)
