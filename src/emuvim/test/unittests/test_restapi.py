# Copyright (c) 2015 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
import unittest
from emuvim.test.api_base import SimpleTestTopology
import subprocess
from emuvim.dcemulator.node import EmulatorCompute
import ast


class testRestApi(SimpleTestTopology):
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

        print('->>>>>>> vim-emu compute start -d datacenter0 -n vnf1 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call(
            "vim-emu compute start -d datacenter0 -n vnf1", shell=True)
        print('->>>>>>> vim-emu compute start -d datacenter0 -n vnf2 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call(
            "vim-emu compute start -d datacenter0 -n vnf2", shell=True)
        print('->>>>>>> vim-emu compute start -d datacenter0 -n vnf3 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        subprocess.call(
            "vim-emu compute start -d datacenter1 -n vnf3", shell=True)
        subprocess.call("vim-emu compute list", shell=True)
        print('->>>>>>> checking running nodes, compute list, and connectivity >>>>>>>>>>')

        # check number of running nodes
        self.assertEqual(len(self.getContainernetContainers()), 3)
        self.assertEqual(len(self.net.hosts), 5)
        self.assertEqual(len(self.net.switches), 2)

        # check compute list result
        self.assertEqual(len(self.dc[0].listCompute()), 2)
        self.assertEqual(len(self.dc[1].listCompute()), 1)
        self.assertTrue(isinstance(
            self.dc[0].listCompute()[0], EmulatorCompute))
        self.assertTrue(isinstance(
            self.dc[0].listCompute()[1], EmulatorCompute))
        self.assertTrue(isinstance(
            self.dc[1].listCompute()[0], EmulatorCompute))
        print("dc1: ", self.dc[0].listCompute())
        print("dc2: ", self.dc[1].listCompute())
        self.assertIn("vnf1", list(map(lambda x: x.name, self.dc[0].listCompute())))
        self.assertIn("vnf2", list(map(lambda x: x.name, self.dc[0].listCompute())))
        self.assertIn("vnf3", list(map(lambda x: x.name, self.dc[1].listCompute())))

        # check connectivity by using ping
        self.assertTrue(self.net.ping(
            [self.dc[0].listCompute()[1], self.dc[0].listCompute()[0]]) <= 0.0)
        self.assertTrue(self.net.ping(
            [self.dc[0].listCompute()[0], self.dc[1].listCompute()[0]]) <= 0.0)
        self.assertTrue(self.net.ping(
            [self.dc[1].listCompute()[0], self.dc[0].listCompute()[1]]) <= 0.0)

        print('network add vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output(
            "vim-emu network add -src vnf1 -dst vnf2 -b -c 10", shell=True)
        print("output: ", output)
        print("type: ", type(output))
        self.assertIn("add-flow", output.decode())
        self.assertIn("success", output.decode())

        print('network remove vnf1 vnf2->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output(
            "vim-emu network remove -src vnf1 -dst vnf2 -b", shell=True)
        self.assertIn("del-flows", output.decode())
        self.assertIn("success", output.decode())

        print('>>>>> checking --> vim-emu compute stop -d datacenter0 -n vnf2 ->>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output(
            "vim-emu compute stop -d datacenter0 -n vnf2", shell=True)

        # check number of running nodes
        self.assertEqual(len(self.getContainernetContainers()), 2)
        self.assertEqual(len(self.net.hosts), 4)
        self.assertEqual(len(self.net.switches), 2)
        # check compute list result
        self.assertEqual(len(self.dc[0].listCompute()), 1)
        self.assertEqual(len(self.dc[1].listCompute()), 1)

        print('>>>>> checking --> vim-emu compute list ->>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output("vim-emu compute list", shell=True)

        # check datacenter list result
        self.assertIn("datacenter0", output.decode())

        print('>>>>> checking --> vim-emu compute status -d datacenter0 -n vnf1 ->>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output(
            "vim-emu compute status -d datacenter0 -n vnf1", shell=True)
        output = ast.literal_eval(output.decode())

        # check compute status result
        self.assertEqual(output["name"], "vnf1")
        self.assertTrue(output["state"]["Running"])

        print('>>>>> checking --> vim-emu datacenter list ->>>>>>>>>>>>>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output("vim-emu datacenter list", shell=True)
        # check datacenter list result
        self.assertIn("datacenter0", output.decode())

        print('->>>>> checking --> vim-emu datacenter status -d datacenter0 ->>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        output = subprocess.check_output(
            "vim-emu datacenter status -d datacenter0", shell=True)
        # check datacenter status result
        self.assertIn("datacenter0", output.decode())
        self.stopApi()
        self.stopNet()


if __name__ == '__main__':
    unittest.main()
