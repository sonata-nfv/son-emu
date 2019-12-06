# Copyright (c) 2018 SONATA-NFV, 5GTANGO and Paderborn University
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
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the 5GTANGO
# partner consortium (www.5gtango.eu).
import logging
import threading
from emuvim.api.tango import llcm


LOG = logging.getLogger("5gtango.llcm")


class TangoLLCMEndpoint(object):
    """
    Creates and starts the 5GTANGO lightweight life cycle manager to simply
    deploy 5GTANGO service packages on the emulator.
    The code is based on SONATA's dummygatekeeper.
    """

    def __init__(self, listenip, port, deploy_sap=False, docker_management=False,
                 auto_deploy=False, auto_delete=False, sap_vnfd_path=None,
                 placement_algorithm_obj=None, env_conf_folder=None):
        self.dcs = {}
        self.ip = listenip
        self.port = port
        llcm.DEPLOY_SAP = deploy_sap
        llcm.USE_DOCKER_MGMT = docker_management
        llcm.AUTO_DEPLOY = auto_deploy
        llcm.AUTO_DELETE = auto_delete
        llcm.SAP_VNFD = sap_vnfd_path
        if placement_algorithm_obj is None:
            # Default placement is RR placement
            placement_algorithm_obj = llcm.RoundRobinDcPlacement()
        llcm.PLACEMENT_ALGORITHM_OBJ = placement_algorithm_obj
        llcm.PER_INSTANCE_ENV_CONFIGURATION_FOLDER = env_conf_folder
        LOG.info("Created 5GTANGO LLCM API endpoint %s" % self)
        LOG.info("Using placement algorithm: {}".format(
                 placement_algorithm_obj))

    def __repr__(self):
        return "%s(%s:%d)" % (self.__class__.__name__, self.ip, self.port)

    def connectDatacenter(self, dc):
        self.dcs[dc.label] = dc
        LOG.debug("Connected DC(%s) to API endpoint %s" % (
            dc, self))

    def start(self):
        thread = threading.Thread(target=self._api_server_thread, args=())
        thread.daemon = True
        thread.start()
        LOG.info("Started API endpoint %s" % self)

    def _api_server_thread(self):
        llcm.start_rest_api(self.ip, self.port, self.dcs)

    def stop(self):
        llcm.stop_rest_api()
