# We need a properly installed Dockernet
from mininet.net import Mininet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.cli import CLI
import mininet.log
import logging
import os
import Pyro4


class RemoteMininetNetwork(object):

    def __init__(self):
        mininet.log.setLogLevel( 'debug' )
        self.net = Mininet( controller=Controller )
        self.net.addController( 'c0' )

    def start(self):
        self.net.start()

    def stop(self):
        CLI(self.net)
        self.net.stop()

    def addHost(self, name, cls=None, **params):
        return str(self.net.addHost(name, cls=cls, **params))

    def addDocker(self, name, **params):
        return str(self.net.addDocker(name, **params))

    def addSwitch(self, name, cls=None, **params):
        return str(self.net.addSwitch(name, cls=cls, **params))

    def addLink(self, node1, node2, port1=None, port2=None,
                cls=None, **params):
        return str(self.net.addLink(node1, node2,
                                    port1, port2, cls=cls, **params))


def start_server():
    daemon = Pyro4.Daemon()
    # ATTENTION:
    # we need a PyroNS instance to be running: pyro4-ns (in new terminal)
    ns = Pyro4.locateNS()
    uri = daemon.register(RemoteMininetNetwork())
    # map object URI to a nice name
    ns.register("remote.mininet", uri)

    logging.info("Server URI is: %s", uri)

    # Start the server...
    daemon.requestLoop()
