# Copyright (c) 2018 SONATA-NFV, 5GTANGO and Paderborn University
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
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the 5GTANGO
# partner consortium (www.5gtango.eu).
import time
import requests
import json
from emuvim.test.base import SimpleTestTopology
from emuvim.api.tango import TangoLLCMEndpoint
from emuvim.api.tango.llcm import initialize_GK, parse_interface
from ipaddress import ip_network


PACKAGE_PATH = "misc/eu.5gtango.emulator-example-service.0.1.tgo"


class testTangoLLCM(SimpleTestTopology):

    #    @unittest.skip("disabled")
    def test_tango_llcm_start_service(self):
        initialize_GK()
        # create network
        self.createNet(nswitches=0, ndatacenter=2, nhosts=2,
                       ndockers=0, enable_learning=True)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.dc[0], self.dc[1])
        self.net.addLink(self.h[1], self.dc[1])
        # connect llcm to data centers
        sdkg1 = TangoLLCMEndpoint("127.0.0.1", 56000)
        sdkg1.connectDatacenter(self.dc[0])
        sdkg1.connectDatacenter(self.dc[1])
        # run the dummy gatekeeper (in another thread, don't block)
        sdkg1.start()
        time.sleep(3)
        # start Mininet network
        self.startNet()
        time.sleep(3)

        # board package
        files = {"package": open(PACKAGE_PATH, "rb")}
        r = requests.post("http://127.0.0.1:56000/packages", files=files)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(json.loads(r.text).get("service_uuid") is not None)

        # instantiate service
        self.service_uuid = json.loads(r.text).get("service_uuid")
        r2 = requests.post("http://127.0.0.1:56000/instantiations",
                           data=json.dumps({"service_uuid": self.service_uuid}))
        self.assertEqual(r2.status_code, 201)

        # give the emulator some time to instantiate everything
        time.sleep(2)

        # check get request APIs
        r3 = requests.get("http://127.0.0.1:56000/packages")
        self.assertEqual(len(json.loads(r3.text)), 1)
        r4 = requests.get("http://127.0.0.1:56000/instantiations")
        self.assertEqual(len(json.loads(r4.text)), 1)

        # check number of running nodes
        self.assertEqual(len(self.getContainernetContainers()), 2)
        self.assertEqual(len(self.net.hosts), 4)
        self.assertEqual(len(self.net.switches), 2)
        # check compute list result (considering placement)
        self.assertEqual(len(self.dc[0].listCompute()), 1)
        self.assertEqual(len(self.dc[1].listCompute()), 1)
        # check connectivity by using ping
        ELAN_list = []

        # check E-Line connection, by checking the IP addresses
        for link in self.net.deployed_elines:
            vnf_src, intf_src = parse_interface(
                link['connection_points_reference'][0])
            print(vnf_src, intf_src)
            src = self.net.getNodeByName(vnf_src)
            if not src:
                continue
            network_list = src.getNetworkStatus()
            src_ip = [intf['ip']
                      for intf in network_list if intf['intf_name'] == intf_src][0]
            src_mask = [intf['netmask']
                        for intf in network_list if intf['intf_name'] == intf_src][0]

            vnf_dst, intf_dst = parse_interface(
                link['connection_points_reference'][1])
            dst = self.net.getNodeByName(vnf_dst)
            if not dst:
                continue
            network_list = dst.getNetworkStatus()
            dst_ip = [intf['ip']
                      for intf in network_list if intf['intf_name'] == intf_dst][0]
            dst_mask = [intf['netmask']
                        for intf in network_list if intf['intf_name'] == intf_dst][0]

            print("src = {0}:{1} ip={2} ".format(
                vnf_src, intf_src, src_ip, src_mask))
            print("dst = {0}:{1} ip={2} ".format(
                vnf_dst, intf_dst, dst_ip, dst_mask))

            # check if the E-Line IP's are in the same subnet
            ret = ip_network(u'{0}'.format(src_ip, src_mask), strict=False)\
                .compare_networks(ip_network(u'{0}'.format(dst_ip, dst_mask), strict=False))
            self.assertTrue(ret == 0)

        for vnf in self.dc[0].listCompute():
            # check E LAN connection
            network_list = vnf.getNetworkStatus()
            mgmt_ip = [intf['ip']
                       for intf in network_list if intf['intf_name'] == 'mgmt']
            self.assertTrue(len(mgmt_ip) > 0)
            ip_address = mgmt_ip[0]
            ELAN_list.append(ip_address)
            print(ip_address)

        # check ELAN connection by ping over the mgmt network (needs to be
        # configured as ELAN in the test service)
        for vnf in self.dc[0].listCompute():
            network_list = vnf.getNetworkStatus()
            mgmt_ip = [intf['ip']
                       for intf in network_list if intf['intf_name'] == 'mgmt']
            self.assertTrue(len(mgmt_ip) > 0)
            ip_address = mgmt_ip[0]
            print(ELAN_list)
            print(ip_address)
            test_ip_list = list(ELAN_list)
            test_ip_list.remove(ip_address)
            for ip in test_ip_list:
                # only take ip address, without netmask
                p = self.net.ping([vnf], manualdestip=ip.split('/')[0])
                print(p)
                self.assertTrue(p <= 0.0)

        # stop Mininet network
        self.stopNet()
        initialize_GK()

    # @unittest.skip("disabled")
    def test_tango_llcm_stop_service(self):
        initialize_GK()
        # create network
        self.createNet(ndatacenter=2, nhosts=2)
        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.dc[0], self.dc[1])
        self.net.addLink(self.h[1], self.dc[1])
        # connect dummy GK to data centers
        sdkg1 = TangoLLCMEndpoint("127.0.0.1", 56001)
        sdkg1.connectDatacenter(self.dc[0])
        sdkg1.connectDatacenter(self.dc[1])
        # run the dummy gatekeeper (in another thread, don't block)
        sdkg1.start()
        time.sleep(3)
        # start Mininet network
        self.startNet()
        time.sleep(3)

        print("starting tests")
        # board package
        files = {"package": open(PACKAGE_PATH, "rb")}
        r = requests.post("http://127.0.0.1:56001/packages", files=files)
        self.assertEqual(r.status_code, 201)
        self.assertTrue(json.loads(r.text).get("service_uuid") is not None)

        # instantiate service
        self.service_uuid = json.loads(r.text).get("service_uuid")
        r2 = requests.post("http://127.0.0.1:56001/instantiations",
                           data=json.dumps({"service_uuid": self.service_uuid}))
        self.assertEqual(r2.status_code, 201)

        # give the emulator some time to instantiate everything
        time.sleep(2)

        # check get request APIs
        r3 = requests.get("http://127.0.0.1:56001/packages")
        self.assertEqual(len(json.loads(r3.text)), 1)
        r4 = requests.get("http://127.0.0.1:56001/instantiations")
        self.assertEqual(len(json.loads(r4.text)), 1)

        # check number of running nodes
        self.assertEqual(len(self.getContainernetContainers()), 2)
        self.assertEqual(len(self.net.hosts), 4)
        self.assertEqual(len(self.net.switches), 2)
        # check compute list result (considering placement)
        self.assertEqual(len(self.dc[0].listCompute()), 1)
        self.assertEqual(len(self.dc[1].listCompute()), 1)

        # stop the service
        service_instance_uuid = json.loads(
            r2.text).get("service_instance_uuid")
        self.assertTrue(service_instance_uuid is not None)
        requests.delete("http://127.0.0.1:56001/instantiations", data=json.dumps(
            {"service_uuid": self.service_uuid, "service_instance_uuid": service_instance_uuid}))

        r5 = requests.get("http://127.0.0.1:56001/instantiations")
        # note that there was 1 instance before
        self.assertEqual(len(json.loads(r5.text)), 0)

        # stop Mininet network
        self.stopNet()
        initialize_GK()
