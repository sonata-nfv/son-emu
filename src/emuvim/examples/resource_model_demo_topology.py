"""
A simple topology to test resource model support.
"""

import logging
import time
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.zerorpc.compute import ZeroRpcApiEndpoint
from emuvim.api.sonata import SonataDummyGatekeeperEndpoint
from emuvim.dcemulator.resourcemodel.upbrm import UpbSimpleCloudDcApproxRM

logging.basicConfig(level=logging.INFO)


def create_topology1():
    # create topology
    # use a maximum of 50% cpu time for containers added to data centers
    net = DCNetwork(dc_emulation_max_cpu=0.5)
    # add some data centers and create a topology
    dc1 = net.addDatacenter("dc1")
    dc2 = net.addDatacenter("dc2")
    s1 = net.addSwitch("s1")
    net.addLink(dc1, s1, delay="10ms")
    net.addLink(dc2, s1, delay="20ms")

    # create and assign resource models for each DC
    rm1 = UpbSimpleCloudDcApproxRM()
    rm2 = UpbSimpleCloudDcApproxRM()
    dc1.assignResourceModel(rm1)
    dc2.assignResourceModel(rm2)

    # add the command line interface endpoint to each DC
    zapi1 = ZeroRpcApiEndpoint("0.0.0.0", 4242)
    zapi1.connectDatacenter(dc1)
    zapi1.connectDatacenter(dc2)
    # run API endpoint server (in another thread, don't block)
    zapi1.start()

    # add the SONATA dummy gatekeeper to each DC
    sdkg1 = SonataDummyGatekeeperEndpoint("0.0.0.0", 8000)
    sdkg1.connectDatacenter(dc1)
    sdkg1.connectDatacenter(dc2)
    # run the dummy gatekeeper (in another thread, don't block)
    sdkg1.start()

    # start the emulation platform
    net.start()
    print "Wait a moment and allocate some compute start some compute resources..."
    time.sleep(2)
    dc1.startCompute("vnf1")
    dc1.startCompute("vnf2", flavor_name="tiny")
    dc1.startCompute("vnf3", flavor_name="small")
    dc2.startCompute("vnf4", flavor_name="medium")
    print "... done."
    time.sleep(2)
    net.CLI()
    net.stop()


def main():
    setLogLevel('info')  # set Mininet loglevel
    create_topology1()


if __name__ == '__main__':
    main()
