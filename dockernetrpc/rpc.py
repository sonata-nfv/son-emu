# We need a properly installed Dockernet
from mininet.net import Mininet
from mininet.node import Controller, Docker, OVSSwitch
from mininet.link import *
from mininet.cli import CLI
import mininet.log
import logging
import os
import zerorpc


class RemoteMininetNetwork(object):

    def __init__(self):
        # set mininet loglevel
        mininet.log.setLogLevel( 'info' )
        self.net = Mininet( controller=Controller )
        self.net.addController( 'c0' )

    def start_net(self):
        self.net.start()

    def CLI(self):
        CLI(self.net)

    def stop_net(self):
        try:
            self.net.stop()
        except Exception as e:
            print e

    def addHost(self, name, ip=None):
        return str(self.net.addHost(name, ip=ip))

    def addDocker(self, name, dimage, ip):
        return str(self.net.addDocker(name, dimage=dimage, ip=ip))

    def addSwitch(self, name):
        # we have to use OVSSwitch to be able to do link attachments
        # at runtime (switch.attach) method
        return str(self.net.addSwitch(name, cls=OVSSwitch))

    def addLink(self, node1, node2, port1=None, port2=None):
        return str(self.net.addLink(node1, node2,
                                    port1, port2))

    def removeHost(self, name):
        return self.net.removeHost(name)

    def removeLink(self, link=None, node1=None, node2=None):
        n1, n2 = self.net.get(node1), self.net.get(node2)
        return self.net.removeLink(node1=n1, node2=n2)


def start_server():
    s = zerorpc.Server(RemoteMininetNetwork())
    s.bind("tcp://0.0.0.0:4242")
    s.run()
