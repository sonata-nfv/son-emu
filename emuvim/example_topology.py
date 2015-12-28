"""
This is an example topology for the distributed cloud emulator (dcemulator).
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>

The original Mininet API has to be completely hidden and not be used by this
script.
"""
import logging
from dcemulator.net import DCNetwork

logging.basicConfig(level=logging.DEBUG)


def create_topology1():
    # initialize network
    net = DCNetwork()

    # add data centers
    dc1 = net.addDatacenter("dc1")
    dc2 = net.addDatacenter("dc2")
    dc3 = net.addDatacenter("dc3")
    dc4 = net.addDatacenter("dc4")
    # add additional SDN switches to our topology
    s1 = net.addSwitch("s1")
    # add links between data centers
    net.addLink(dc1, dc2)
    net.addLink("dc1", s1)
    net.addLink(s1, "dc3")
    net.addLink(s1, dc4)
    # start network
    net.start()
    net.CLI()  # TODO remove this when we integrate APIs?
    net.stop()  # TODO remove this when we integrate APIs?
    # start APIs (to access emulated cloud data centers)
    pass  # TODO: how to reflect one API endpoint per DC?


def main():
    create_topology1()


if __name__ == '__main__':
    main()
