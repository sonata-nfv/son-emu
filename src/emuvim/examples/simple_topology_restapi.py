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
    1. Create a data center network object (DCNetwork)
    """
    net = DCNetwork(monitor=True, enable_learning=False)

    """
    1b. add a monitoring agent to the DCNetwork
    """
    #keep old zeroRPC interface to test the prometheus metric query
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
    dc3 = net.addDatacenter("long_data_center_name3")
    dc4 = net.addDatacenter(
        "datacenter4",
        metadata={"mydata": "we can also add arbitrary metadata to each DC"})

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
    net.addLink(dc1, dc2)
    net.addLink("datacenter1", s1)
    net.addLink(s1, dc3)
    net.addLink(s1, "datacenter4")

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
    api1 = RestApiEndpoint("127.0.0.1", 5000)
    # connect data centers to this endpoint
    api1.connectDatacenter(dc1)
    api1.connectDatacenter(dc2)
    api1.connectDatacenter(dc3)
    api1.connectDatacenter(dc4)
    # connect total network also, needed to do the chaining and monitoring
    api1.connectDCNetwork(net)
    # run API endpoint server (in another thread, don't block)
    api1.start()

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
