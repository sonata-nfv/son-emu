"""
Test suite to automatically test emulator REST API endpoints.
"""

import time
import unittest
from emuvim.test.api_base import SimpleTestTopology
import subprocess

class testRestApi( SimpleTestTopology ):
    """
    Tests to check the REST API endpoints of the emulator.
    """

    def testRestApi(self):

        # create network
        self.createNet(nswitches=0, ndatacenter=2, nhosts=2, ndockers=0)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[1])
        self.net.addLink(self.dc[0], self.dc[1])
        # start api
        self.startApi()
        # start Mininet network
        self.startNet()
        print('compute start datacenter0, vnf1 ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute start -d datacenter0 -n vnf1", shell=True)
        print('compute start datacenter0, vnf2 ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute start -d datacenter0 -n vnf2", shell=True)
        print('compute start datacenter1, vnf3 ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute start -d datacenter1 -n vnf3", shell=True)
        print('compute list ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute list", shell=True)

        print('network add vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli network add -src vnf1 -dst vnf2 -b -c 10", shell=True)
        print('network remove vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli network remove -src vnf1 -dst vnf2 -b", shell=True)

        print('compute stop datacenter0, vnf2 ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute stop -d datacenter0 -n vnf2", shell=True)
        print('compute list ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute list", shell=True)
        print('compute status datacenter0, vnf1 ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli compute status -d datacenter0 -n vnf1", shell=True)
        print('datacenter list ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli datacenter list", shell=True)
        print('datacenter status datacenter0 ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call("son-emu-cli datacenter status -d datacenter0", shell=True)
        self.stopNet()


if __name__ == '__main__':
    unittest.main()
