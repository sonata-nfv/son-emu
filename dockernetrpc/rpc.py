# We need a properly installed Dockernet
from mininet.net import Mininet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.link import *
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

    def CLI(self):
        CLI(self.net)

    def stop(self):
        try:
            self.net.stop()
        except Exception as e:
            print e


    def addHost(self, name, cls=None, **params):
        return str(self.net.addHost(name, cls=cls, **params))

    def addDocker(self, name, **params):
        return str(self.net.addDocker(name, **params))

    def addSwitch(self, name, **params):
        # we have to use OVSSwitch to be able to do link attachments
        # at runtime (switch.attach) method
        return str(self.net.addSwitch(name, cls=OVSSwitch, **params))

    def addLink(self, node1, node2, port1=None, port2=None,
                cls=None, **params):
        return str(self.net.addLink(node1, node2,
                                    port1, port2, cls=cls, **params))

    def removeHost(self, name, **params):
        return self.net.removeHost(name, **params)

    def removeLink(self, link=None, node1=None, node2=None):
        n1, n2 = self.net.get(node1), self.net.get(node2)
        return self.net.removeLink(node1=n1, node2=n2)


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
