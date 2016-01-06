"""
This is an example topology for the distributed cloud emulator (dcemulator).
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>

The original Mininet API has to be completely hidden and not be used by this
script.
"""
import logging
from dcemulator.net import DCNetwork
from api.zerorpcapi import ZeroRpcApiEndpoint

logging.basicConfig(level=logging.DEBUG)


def create_topology1():
    # TODO add long comments to this example to show people how to use this
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

    # create and start APIs (to access emulated cloud data centers)
    zapi1 = ZeroRpcApiEndpoint("0.0.0.0", 4242)
    zapi1.connectDatacenter(dc1)
    zapi1.connectDatacenter(dc2)
    zapi1.start()
    # lets also create a second API endpoint on another port to
    # demonstrate hat you can have one endpoint for each of
    # your data centers
    zapi2 = ZeroRpcApiEndpoint("0.0.0.0", 4343)
    zapi2.connectDatacenter(dc3)
    zapi2.connectDatacenter(dc4)
    zapi2.start()

    # start network
    net.start()
    net.CLI()  # TODO remove this when we integrate APIs?
    net.stop()  # TODO remove this when we integrate APIs?


def main():
    create_topology1()


if __name__ == '__main__':
    main()
