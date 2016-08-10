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
A simple topology with two PoPs for the y1 demo story board.

        (dc1) <<-->> s1 <<-->> (dc2)
"""

import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint
from emuvim.api.sonata import SonataDummyGatekeeperEndpoint
from mininet.node import RemoteController
import signal
import sys
import time

logging.basicConfig(level=logging.INFO)

exit = False

def create_topology1():

    global exit

    # create topology
    net = DCNetwork(controller=RemoteController, monitor=True, enable_learning = False)
    dc1 = net.addDatacenter("dc1")
    dc2 = net.addDatacenter("dc2")
    s1 = net.addSwitch("s1")
    net.addLink(dc1, s1, delay="10ms")
    net.addLink(dc2, s1, delay="20ms")

    # add the command line interface endpoint to each DC (REST API)
    rapi1 = RestApiEndpoint("0.0.0.0", 5001)
    rapi1.connectDatacenter(dc1)
    rapi1.connectDatacenter(dc2)
    # connect total network also, needed to do the chaining and monitoring
    rapi1.connectDCNetwork(net)
    # run API endpoint server (in another thread, don't block)
    rapi1.start()

    # add the SONATA dummy gatekeeper to each DC
    sdkg1 = SonataDummyGatekeeperEndpoint("0.0.0.0", 5000)
    sdkg1.connectDatacenter(dc1)
    sdkg1.connectDatacenter(dc2)
    # run the dummy gatekeeper (in another thread, don't block)
    sdkg1.start()

    # start the emulation platform
    net.start()
    
    #does not work from docker compose (cannot start container in interactive mode)
    #cli = net.CLI()
    # instead wait here:
    logging.info("waiting for SIGTERM or SIGINT signal")
    while not exit:
        time.sleep(1)
    logging.info("got SIG signal")
    net.stop()

def exit_gracefully(signum, frame):
    """
    7. At shutdown, we should receive the unix signal here and shutdown gracefully
    """

    global exit

    logging.info('Signal handler called with signal {0}'.format(signum))
    exit = True


def main():
    setLogLevel('info')  # set Mininet loglevel
    # add the SIGTERM handler (eg. received when son-emu docker container stops)
    signal.signal(signal.SIGTERM, exit_gracefully)
    # also handle Ctrl-C
    signal.signal(signal.SIGINT, exit_gracefully)
    # start the topology
    create_topology1()


if __name__ == '__main__':
    main()
