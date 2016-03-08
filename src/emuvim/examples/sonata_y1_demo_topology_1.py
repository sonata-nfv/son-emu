"""
A simple topology with two PoPs for the y1 demo story board.

        (dc1) <<-->> s1 <<-->> (dc2)
"""

import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.zerorpc.compute import ZeroRpcApiEndpoint

logging.basicConfig(level=logging.INFO)


def create_topology1():
    # create topology
    net = DCNetwork()
    dc1 = net.addDatacenter("dc1")
    dc2 = net.addDatacenter("dc2")
    s1 = net.addSwitch("s1")
    net.addLink(dc1, s1)
    net.addLink(dc2, s1)

    # create a new instance of a endpoint implementation
    zapi1 = ZeroRpcApiEndpoint("0.0.0.0", 4242)
    # connect data centers to this endpoint
    zapi1.connectDatacenter(dc1)
    zapi1.connectDatacenter(dc2)
    # run API endpoint server (in another thread, don't block)
    zapi1.start()

    # TODO add "fake gatekeeper" api endpoint and connect it to both dcs

    # start the emulation platform
    net.start()
    net.CLI()
    net.stop()


def main():
    setLogLevel('info')  # set Mininet loglevel
    create_topology1()


if __name__ == '__main__':
    main()