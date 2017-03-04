"""
Copyright (c) 2015 SONATA-NFV
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
"""
A simple topology with a single data center for usage in son-profile.

"""

import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.sonata import SonataDummyGatekeeperEndpoint
from mininet.node import RemoteController
from time import sleep
import argparse
import sys
import signal

logging.basicConfig()
LOG = logging.getLogger("sonata-profiling")
LOG.setLevel(logging.DEBUG)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

"""
    Catches SIGINT and SIGTERM to shut the topology down gracefully.
"""
class GracefulKiller:
    def __init__(self, to_be_killed):
        signal.signal(signal.SIGINT, self.exit_gracefully)
        signal.signal(signal.SIGTERM, self.exit_gracefully)
        self.to_be_killed = to_be_killed

    def exit_gracefully(self, signum, frame):
        self.to_be_killed.stop_it()


"""
    A simple topology with only one data center which will stop when another thread tells it to or when a time limit is reached.
    :args: an argument list which may contain the time limit
"""
class Profiling:

    stop_now = False

    """
     Set up a simple topology and start it
    """
    def __init__(self):
        GracefulKiller(self)
        # create topology
        self.net = DCNetwork(controller=RemoteController, monitor=False, enable_learning=False)
        self.dc = self.net.addDatacenter("dc1")

        # add the command line interface endpoint to each DC (REST API)
        self.rapi1 = RestApiEndpoint("0.0.0.0", 5001)
        self.rapi1.connectDCNetwork(self.net)
        self.rapi1.connectDatacenter(self.dc)
        # run API endpoint server (in another thread, don't block)
        self.rapi1.start()

        # add the SONATA dummy gatekeeper to each DC
        self.sdkg1 = SonataDummyGatekeeperEndpoint("0.0.0.0", 5000, deploy_sap=False)
        self.sdkg1.connectDatacenter(self.dc)
        # run the dummy gatekeeper (in another thread, don't block)
        self.sdkg1.start()


        self.net.start()
        LOG.info("Started topology")
        while(not self.stop_now):
            sleep(1)
        self.net.stop()
        LOG.info("Stopped topology")

    """
     Set stop value to stop the topology
    """
    def stop_it(self):
        self.stop_now = True


def main(args):
    setLogLevel('info')  # set Mininet loglevel
    p = Profiling()


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Run a simple topology")
    parser.add_argument('--time', '-t', metavar='seconds', type=float, help='a time limit', default=-1, required=False, dest='time')
    arg_list = vars(parser.parse_args(sys.argv[1:]))
    main(arg_list)
