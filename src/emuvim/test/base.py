"""
Helper module that implements helpers for test implementations.
"""

import unittest
import os
import subprocess
import docker
from emuvim.dcemulator.net import DCNetwork
from mininet.clean import cleanup
from mininet.node import Controller

class SimpleTestTopology(unittest.TestCase):
    """
        Helper class to do basic test setups.
        s1 -- s2 -- s3 -- ... -- sN
    """

    def __init__(self, *args, **kwargs):
        self.net = None
        self.s = []   # list of switches
        self.h = []   # list of hosts
        self.d = []   # list of docker containers
        self.dc = []  # list of data centers
        self.docker_cli = None
        super(SimpleTestTopology, self).__init__(*args, **kwargs)

    def createNet(
            self,
            nswitches=0, ndatacenter=0, nhosts=0, ndockers=0,
            autolinkswitches=False):
        """
        Creates a Mininet instance and automatically adds some
        nodes to it.
        """
        self.net = DCNetwork()

        # add some switches
        for i in range(0, nswitches):
            self.s.append(self.net.addSwitch('s%d' % i))
        # if specified, chain all switches
        if autolinkswitches:
            for i in range(0, len(self.s) - 1):
                self.net.addLink(self.s[i], self.s[i + 1])
        # add some data centers
        for i in range(0, ndatacenter):
            self.dc.append(
                self.net.addDatacenter(
                    'datacenter%d' % i,
                    metadata={"unittest_dc": i}))
        # add some hosts
        for i in range(0, nhosts):
            self.h.append(self.net.addHost('h%d' % i))
        # add some dockers
        for i in range(0, ndockers):
            self.d.append(self.net.addDocker('d%d' % i, dimage="ubuntu"))

    def startNet(self):
        self.net.start()

    def stopNet(self):
        self.net.stop()

    def getDockerCli(self):
        """
        Helper to interact with local docker instance.
        """
        if self.docker_cli is None:
            self.docker_cli = docker.Client(
                base_url='unix://var/run/docker.sock')
        return self.docker_cli

    def getDockernetContainers(self):
        """
        List the containers managed by dockernet
        """
        return self.getDockerCli().containers(filters={"label": "com.dockernet"})

    @staticmethod
    def setUp():
        pass

    @staticmethod
    def tearDown():
        cleanup()
        # make sure that all pending docker containers are killed
        with open(os.devnull, 'w') as devnull:
            subprocess.call(
                "sudo docker rm -f $(sudo docker ps --filter 'label=com.dockernet' -a -q)",
                stdout=devnull,
                stderr=devnull,
                shell=True)