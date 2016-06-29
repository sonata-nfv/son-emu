"""
This is an example topology for the distributed cloud emulator (dcemulator).
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>


This is an example that shows how a user of the emulation tool can
define network topologies with multiple emulated cloud data centers.

The definition is done with a Python API which looks very similar to the
Mininet API (in fact it is a wrapper for it).

We only specify the topology *between* data centers not within a single
data center (data center internal setups or placements are not of interest,
we want to experiment with VNF chains deployed across multiple PoPs).

The original Mininet API has to be completely hidden and not be used by this
script.
"""
import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork

from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint

from emuvim.api.zerorpc.compute import ZeroRpcApiEndpoint
from emuvim.api.zerorpc.network import ZeroRpcApiEndpointDCNetwork


logging.basicConfig(level=logging.INFO)


def create_topology1():
    """
    1. Create a data center network object (DCNetwork) with monitoring enabled
    """
    net = DCNetwork(monitor=True, enable_learning=False)

    """
    1b. Add endpoint APIs for the whole DCNetwork,
        to access and control the networking from outside.
        e.g., to setup forwarding paths between compute
        instances aka. VNFs (represented by Docker containers), passing through
        different switches and datacenters of the emulated topology
    """
    mon_api = ZeroRpcApiEndpointDCNetwork("0.0.0.0", 5151)
    mon_api.connectDCNetwork(net)
    mon_api.start()

    """
    2. Add (logical) data centers to the topology
       (each data center is one "bigswitch" in our simplified
        first prototype)
    """
    dc1 = net.addDatacenter("datacenter1")
    dc2 = net.addDatacenter("datacenter2")

    """
    3. You can add additional SDN switches for data center
       interconnections to the network.
    """
    s1 = net.addSwitch("s1")

    """
    4. Add links between your data centers and additional switches
       to define you topology.
       These links can use Mininet's features to limit bw, add delay or jitter.
    """

    net.addLink(dc1, s1)
    net.addLink(s1, dc2)


    """
    5. We want to access and control our data centers from the outside,
       e.g., we want to connect an orchestrator to start/stop compute
       resources aka. VNFs (represented by Docker containers in the emulated)

       So we need to instantiate API endpoints (e.g. a zerorpc or REST
       interface). Depending on the endpoint implementations, we can connect
       one or more data centers to it, which can then be controlled through
       this API, e.g., start/stop/list compute instances.
    """
    # keep the old zeroRPC interface for the prometheus metric query test
    zapi1 = ZeroRpcApiEndpoint("0.0.0.0", 4242)
    # connect data centers to this endpoint
    zapi1.connectDatacenter(dc1)
    zapi1.connectDatacenter(dc2)
    # run API endpoint server (in another thread, don't block)
    zapi1.start()

    # create a new instance of a endpoint implementation
    api1 = RestApiEndpoint("0.0.0.0", 5000)
    # connect data centers to this endpoint
    api1.connectDatacenter(dc1)
    api1.connectDatacenter(dc2)
    # connect total network also, needed to do the chaining and monitoring
    api1.connectDCNetwork(net)
    # run API endpoint server (in another thread, don't block)
    api1.start()

    """
    5.1. For our example, we create a second endpoint to illustrate that
         this is supported by our design. This feature allows us to have
         one API endpoint for each data center. This makes the emulation
         environment more realistic because you can easily create one
         OpenStack-like REST API endpoint for *each* data center.
         This will look like a real-world multi PoP/data center deployment
         from the perspective of an orchestrator.
    """
    #zapi2 = ZeroRpcApiEndpoint("0.0.0.0", 4343)
    #zapi2.connectDatacenter(dc3)
    #zapi2.connectDatacenter(dc4)
    #zapi2.start()

    """
    6. Finally we are done and can start our network (the emulator).
       We can also enter the Mininet CLI to interactively interact
       with our compute resources (just like in default Mininet).
       But we can also implement fully automated experiments that
       can be executed again and again.
    """
    net.start()
    net.CLI()
    # when the user types exit in the CLI, we stop the emulator
    net.stop()


def main():
    setLogLevel('info')  # set Mininet loglevel
    create_topology1()


if __name__ == '__main__':
    main()
