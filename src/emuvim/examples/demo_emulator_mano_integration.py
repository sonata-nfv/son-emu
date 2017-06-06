import logging
from mininet.log import setLogLevel
from emuvim.dcemulator.net import DCNetwork
from emuvim.api.openstack.openstack_api_endpoint import OpenstackApiEndpoint
from emuvim.api.rest.rest_api_endpoint import RestApiEndpoint


logging.basicConfig(level=logging.INFO)
setLogLevel('info')  # set Mininet loglevel
logging.getLogger('werkzeug').setLevel(logging.DEBUG)


class DemoTopology(DCNetwork):
    """
    This is a 2x2 PoP topology used for the emulator MANO integration demo.
    """

    def __init__(self):
        """
        Initialize multi PoP emulator network.
        """
        super(DemoTopology, self).__init__(
            monitor=True,
            enable_learning=True
        )
        # define members for later use
        self.pop1 = None
        self.pop2 = None
        self.pop3 = None
        self.pop4 = None
        self.sw1 = None
        self.sw2 = None

    def setup(self):
        self._create_switches()
        self._create_pops()
        self._create_links()
        self._create_rest_api_endpoints()
        self._create_openstack_api_endpoints()

    def _create_switches(self):
        self.sw1 = self.addSwitch("s1")
        self.sw2 = self.addSwitch("s2")

    def _create_pops(self):
        # two PoPs for the SONATA SP
        self.pop1 = self.addDatacenter("sonata-pop1")
        self.pop2 = self.addDatacenter("sonata-pop2")
        # two PoPs for the OSM SP
        self.pop3 = self.addDatacenter("osm-pop1")
        self.pop4 = self.addDatacenter("osm-pop2")

    def _create_links(self):
        # SONATA island
        self.addLink(self.pop1, self.sw1, delay="10ms")
        self.addLink(self.pop2, self.sw1, delay="10ms")
        # OSM island
        self.addLink(self.pop3, self.sw2, delay="10ms")
        self.addLink(self.pop4, self.sw2, delay="10ms")

    def _create_openstack_api_endpoints(self):
        # create
        api1 = OpenstackApiEndpoint("0.0.0.0", 6001)
        api2 = OpenstackApiEndpoint("0.0.0.0", 6002)
        api3 = OpenstackApiEndpoint("0.0.0.0", 6003)
        api4 = OpenstackApiEndpoint("0.0.0.0", 6004)
        # connect PoPs
        api1.connect_datacenter(self.pop1)
        api2.connect_datacenter(self.pop2)
        api3.connect_datacenter(self.pop3)
        api4.connect_datacenter(self.pop4)
        # connect network
        api1.connect_dc_network(self)
        api2.connect_dc_network(self)
        api3.connect_dc_network(self)
        api4.connect_dc_network(self)
        # start
        api1.start()
        api2.start()
        api3.start()
        api4.start()

    def _create_rest_api_endpoints(self):
        # create
        apiR = RestApiEndpoint("0.0.0.0", 5001)
        # connect PoPs
        apiR.connectDatacenter(self.pop1)
        apiR.connectDatacenter(self.pop2)
        apiR.connectDatacenter(self.pop3)
        apiR.connectDatacenter(self.pop4)
        # connect network
        apiR.connectDCNetwork(self)
        # start
        apiR.start()


def main():
    t = DemoTopology()
    t.setup()
    t.start()
    t.CLI()
    t.stop()


if __name__ == '__main__':
    main()
