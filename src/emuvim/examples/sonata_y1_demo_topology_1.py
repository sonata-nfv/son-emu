"""
A simple topology with two PoPs for the y1 demo story board.

        (dc1) <<-->> s1 <<-->> (dc2)
"""

import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.zerorpc.compute import ZeroRpcApiEndpoint
from emuvim.api.sonata import SonataDummyGatekeeperEndpoint

logging.basicConfig(level=logging.INFO)


def create_topology1():
    # create topology
    net = DCNetwork()
    dc1 = net.addDatacenter("dc1")
    dc2 = net.addDatacenter("dc2")
    s1 = net.addSwitch("s1")
    net.addLink(dc1, s1, delay="10ms")
    net.addLink(dc2, s1, delay="20ms")

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
    net.CLI()
    net.stop()


def main():
    setLogLevel('info')  # set Mininet loglevel
    create_topology1()


if __name__ == '__main__':
    main()