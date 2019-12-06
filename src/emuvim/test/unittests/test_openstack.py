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
import os
import unittest
import requests
import simplejson as json
import yaml

from emuvim.test.api_base_openstack import ApiBaseOpenStack


class testRestApi(ApiBaseOpenStack):
    """
    Tests to check the REST API endpoints of the emulator.
    """

    def setUp(self):
        # create network
        self.createNet(nswitches=3, ndatacenter=2, nhosts=2,
                       ndockers=0, autolinkswitches=True)

        # setup links
        self.net.addLink(self.dc[0], self.h[0])
        self.net.addLink(self.h[1], self.dc[1])
        self.net.addLink(self.dc[0], self.dc[1])

        # start api
        self.startApi()

        # start Mininet network
        self.startNet()

    def testNovaDummy(self):
        print('->>>>>>> test Nova Dummy Class->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(" ")

        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open(os.path.join(os.path.dirname(
            __file__), "templates/test_heatapi_template_create_stack.yml")).read()
        url = "http://0.0.0.0:18004/v1/tenantabc123/stacks"
        requests.post(url, data=json.dumps(yaml.load(test_heatapi_template_create_stack)),
                      headers=headers)

        print('->>>>>>> test Nova List Versions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/"
        listapiversionnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionnovaresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionnovaresponse.content)[
                         "versions"][0]["id"], "v2.1")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)[
                         "versions"][0]["status"], "CURRENT")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)[
                         "versions"][0]["version"], "2.38")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)[
                         "versions"][0]["min_version"], "2.1")
        self.assertEqual(json.loads(listapiversionnovaresponse.content)[
                         "versions"][0]["updated"], "2013-07-23T11:33:21Z")
        print(" ")

        print('->>>>>>> test Nova Version Show ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla"
        listapiversion21novaresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversion21novaresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversion21novaresponse.content)[
                         "version"]["id"], "v2.1")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)[
                         "version"]["status"], "CURRENT")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)[
                         "version"]["version"], "2.38")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)[
                         "version"]["min_version"], "2.1")
        self.assertEqual(json.loads(listapiversion21novaresponse.content)[
                         "version"]["updated"], "2013-07-23T11:33:21Z")
        print(" ")

        print('->>>>>>> test Nova Version List Server APIs ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers"
        listserverapisnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisnovaresponse.status_code, 200)
        self.assertNotEqual(json.loads(listserverapisnovaresponse.content)[
                            "servers"][0]["name"], "")
        print(" ")

        print('->>>>>>> test Nova Delete Server APIs ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers/%s" % (
            json.loads(listserverapisnovaresponse.content)["servers"][0]["id"])
        deleteserverapisnovaresponse = requests.delete(url, headers=headers)
        self.assertEqual(deleteserverapisnovaresponse.status_code, 204)
        print(" ")

        print('->>>>>>> test Nova Delete Non-Existing Server APIs ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers/non-existing-ix"
        deleteserverapisnovaresponse = requests.delete(url, headers=headers)
        self.assertEqual(deleteserverapisnovaresponse.status_code, 404)
        print(" ")

        print('->>>>>>> testNovaVersionListServerAPIs_withPortInformation ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers/andPorts"
        listserverapisnovaresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisnovaresponse.status_code, 200)
        self.assertNotEqual(json.loads(listserverapisnovaresponse.content)[
                            "servers"][0]["name"], "")
        print(" ")

        print('->>>>>>> test Nova List Flavors ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/flavors"
        listflavorsresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsresponse.status_code, 200)
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][0]["name"], [
                      "m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][1]["name"], [
                      "m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsresponse.content)["flavors"][2]["name"], [
                      "m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        print(" ")

        print('->>>>>>> testNovaAddFlavors ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/flavors"
        addflavorsresponse = requests.post(url,
                                           data='{"flavor":{"name": "testFlavor", "vcpus": "test_vcpus", "ram": 1024, "disk": 10}}',
                                           headers=headers)
        self.assertEqual(addflavorsresponse.status_code, 200)
        self.assertIsNotNone(json.loads(
            addflavorsresponse.content)["flavor"]["id"])
        self.assertIsNotNone(json.loads(addflavorsresponse.content)[
                             "flavor"]["links"][0]['href'])
        print(" ")

        print('->>>>>>> test Nova List Flavors Detail ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/flavors/detail"
        listflavorsdetailresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsdetailresponse.status_code, 200)
        self.assertIn(json.loads(listflavorsdetailresponse.content)[
                      "flavors"][0]["name"], ["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsdetailresponse.content)[
                      "flavors"][1]["name"], ["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        self.assertIn(json.loads(listflavorsdetailresponse.content)[
                      "flavors"][2]["name"], ["m1.nano", "m1.tiny", "m1.micro", "m1.small"])
        print(" ")

        print('->>>>>>> testNovaAddFlavors ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/flavors/detail"
        addflavorsresponse = requests.post(url,
                                           data='{"flavor":{"name": "testFlavor", "vcpus": "test_vcpus", "ram": 1024, "disk": 10}}',
                                           headers=headers)
        self.assertEqual(addflavorsresponse.status_code, 200)
        self.assertIsNotNone(json.loads(
            addflavorsresponse.content)["flavor"]["id"])
        self.assertIsNotNone(json.loads(addflavorsresponse.content)[
                             "flavor"]["links"][0]['href'])
        print(" ")

        print('->>>>>>> test Nova List Flavor By Id ->>>>>>>>>>>>>>>')

        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/flavors/%s" % (
            json.loads(listflavorsdetailresponse.content)["flavors"][0]["name"])
        listflavorsbyidresponse = requests.get(url, headers=headers)
        self.assertEqual(listflavorsbyidresponse.status_code, 200)
        self.assertEqual(json.loads(listflavorsbyidresponse.content)[
                         "flavor"]["id"], json.loads(listflavorsdetailresponse.content)["flavors"][0]["id"])
        print(" ")

        print('->>>>>>> test Nova List Images ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/images"
        listimagesresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagesresponse.status_code, 200)
        print(listimagesresponse.content)
        print(" ")

        print('->>>>>>> test Nova List Images Details ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/images/detail"
        listimagesdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagesdetailsresponse.status_code, 200)
        self.assertEqual(json.loads(listimagesdetailsresponse.content)[
                         "images"][0]["metadata"]["architecture"], "x86_64")
        print(" ")

        print('->>>>>>> test Nova List Image By Id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/images/%s" % (
            json.loads(listimagesdetailsresponse.content)["images"][0]["id"])
        listimagebyidresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagebyidresponse.status_code, 200)
        self.assertEqual(json.loads(listimagebyidresponse.content)[
                         "image"]["id"], json.loads(listimagesdetailsresponse.content)["images"][0]["id"])
        print(" ")

        print('->>>>>>> test Nova List Image By Non-Existend Id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/images/non_existing_id"
        listimagebynonexistingidresponse = requests.get(url, headers=headers)
        self.assertEqual(listimagebynonexistingidresponse.status_code, 404)
        print(" ")

        # find ubuntu id
        for image in json.loads(listimagesresponse.content)["images"]:
            if image["name"] == "ubuntu:trusty":
                ubuntu_image_id = image["id"]

        print('->>>>>>> test Nova Create Server Instance ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers"
        data = '{"server": {"name": "X", "flavorRef": "%s", "imageRef":"%s"}}' % (
            json.loads(listflavorsresponse.content)["flavors"][0]["id"], ubuntu_image_id)
        createserverinstance = requests.post(url, data=data, headers=headers)
        self.assertEqual(createserverinstance.status_code, 200)
        self.assertEqual(json.loads(createserverinstance.content)[
                         "server"]["image"]["id"], ubuntu_image_id)
        print(" ")

        print('->>>>>>> test Nova Create Server Instance With Already Existing Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers"
        data = '{"server": {"name": "X", "flavorRef": "%s", "imageRef":"%s"}}' % (
            json.loads(listflavorsresponse.content)["flavors"][0]["id"], ubuntu_image_id)
        createserverinstance = requests.post(url, data=data, headers=headers)
        self.assertEqual(createserverinstance.status_code, 409)
        print(" ")

        print('->>>>>>> test Nova Version List Server APIs Detailed ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers/detail"
        listserverapisdetailedresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverapisdetailedresponse.status_code, 200)
        self.assertEqual(json.loads(listserverapisdetailedresponse.content)[
                         "servers"][0]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> test Nova Show Server Details ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers/%s" % (
            json.loads(listserverapisdetailedresponse.content)["servers"][0]["id"])
        listserverdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(listserverdetailsresponse.status_code, 200)
        self.assertEqual(json.loads(listserverdetailsresponse.content)[
                         "server"]["flavor"]["links"][0]["rel"], "bookmark")
        print(" ")

        print('->>>>>>> test Nova Show Non-Existing Server Details ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18774/v2.1/id_bla/servers/non_existing_server_id"
        listnonexistingserverdetailsresponse = requests.get(
            url, headers=headers)
        self.assertEqual(listnonexistingserverdetailsresponse.status_code, 404)
        print(" ")

    def testNeutronDummy(self):
        print('->>>>>>> test Neutron Dummy Class->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(" ")

        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open(os.path.join(os.path.dirname(
            __file__), "templates/test_heatapi_template_create_stack.yml")).read()
        url = "http://0.0.0.0:18004/v1/tenantabc123/stacks"
        requests.post(url, data=json.dumps(
            yaml.load(test_heatapi_template_create_stack)), headers=headers)
        # test_heatapi_keystone_get_token = open("test_heatapi_keystone_get_token.json").read()

        print('->>>>>>> test Neutron List Versions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionstackresponse.content)[
                         "versions"][0]["id"], "v2.0")
        print(" ")

        print('->>>>>>> test Neutron Show API v2.0 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0"
        listapiversionv20response = requests.get(url, headers=headers)
        self.assertEqual(listapiversionv20response.status_code, 200)
        self.assertEqual(json.loads(listapiversionv20response.content)[
                         "resources"][0]["name"], "subnet")
        self.assertEqual(json.loads(listapiversionv20response.content)[
                         "resources"][1]["name"], "network")
        self.assertEqual(json.loads(listapiversionv20response.content)[
                         "resources"][2]["name"], "ports")
        print(" ")

        print('->>>>>>> test Neutron List Networks ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks"
        listnetworksesponse1 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse1.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse1.content)[
                         "networks"][0]["status"], "ACTIVE")
        listNetworksId = json.loads(listnetworksesponse1.content)[
            "networks"][0]["id"]
        listNetworksName = json.loads(listnetworksesponse1.content)[
            "networks"][0]["name"]
        listNetworksId2 = json.loads(listnetworksesponse1.content)[
            "networks"][1]["id"]
        print(" ")

        print('->>>>>>> test Neutron List Non-Existing Networks ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks?name=non_existent_network_name"
        listnetworksesponse2 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse2.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron List Networks By Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        # tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest
        url = "http://0.0.0.0:19696/v2.0/networks?name=" + listNetworksName
        listnetworksesponse3 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse3.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse3.content)[
                         "networks"][0]["name"], listNetworksName)
        print(" ")

        print('->>>>>>> test Neutron List Networks By Id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        # tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest
        url = "http://0.0.0.0:19696/v2.0/networks?id=" + listNetworksId
        listnetworksesponse4 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse4.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse4.content)[
                         "networks"][0]["id"], listNetworksId)
        print(" ")

        print('->>>>>>> test Neutron List Networks By Multiple Ids ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks?id=" + listNetworksId + "&id=" + \
            listNetworksId2  # tcpdump-vnf:input:net:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest
        listnetworksesponse5 = requests.get(url, headers=headers)
        self.assertEqual(listnetworksesponse5.status_code, 200)
        self.assertEqual(json.loads(listnetworksesponse5.content)[
                         "networks"][0]["id"], listNetworksId)
        self.assertEqual(json.loads(listnetworksesponse5.content)[
                         "networks"][1]["id"], listNetworksId2)
        print(" ")

        print('->>>>>>> test Neutron Show Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks/" + listNetworksId
        shownetworksesponse = requests.get(url, headers=headers)
        self.assertEqual(shownetworksesponse.status_code, 200)
        self.assertEqual(json.loads(shownetworksesponse.content)[
                         "network"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> test Neutron Show Network Non-ExistendNetwork ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks/non_existent_network_id"
        shownetworksesponse2 = requests.get(url, headers=headers)
        self.assertEqual(shownetworksesponse2.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Create Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks"
        createnetworkresponse = requests.post(
            url, data='{"network": {"name": "sample_network","admin_state_up": true}}', headers=headers)
        self.assertEqual(createnetworkresponse.status_code, 201)
        self.assertEqual(json.loads(createnetworkresponse.content)[
                         "network"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> test Neutron Create Network With Existing Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks"
        createnetworkresponsefailure = requests.post(
            url, data='{"network": {"name": "sample_network","admin_state_up": true}}', headers=headers)
        self.assertEqual(createnetworkresponsefailure.status_code, 400)
        print(" ")

        print('->>>>>>> test Neutron Update Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks/%s" % (
            json.loads(createnetworkresponse.content)["network"]["id"])
        updatenetworkresponse = requests.put(
            url, data='{"network": {"status": "ACTIVE", "admin_state_up":true, "tenant_id":"abcd123", "name": "sample_network_new_name", "shared":false}}', headers=headers)
        self.assertEqual(updatenetworkresponse.status_code, 200)
        self.assertEqual(json.loads(updatenetworkresponse.content)[
                         "network"]["name"], "sample_network_new_name")
        self.assertEqual(json.loads(updatenetworkresponse.content)[
                         "network"]["tenant_id"], "abcd123")
        print(" ")

        print('->>>>>>> test Neutron Update Non-Existing Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/networks/non-existing-name123"
        updatenetworkresponse = requests.put(
            url, data='{"network": {"name": "sample_network_new_name"}}', headers=headers)
        self.assertEqual(updatenetworkresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron List Subnets ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets"
        listsubnetsresponse = requests.get(url, headers=headers)
        listSubnetName = json.loads(listsubnetsresponse.content)[
            "subnets"][0]["name"]
        listSubnetId = json.loads(listsubnetsresponse.content)[
            "subnets"][0]["id"]
        listSubnetId2 = json.loads(listsubnetsresponse.content)[
            "subnets"][1]["id"]
        self.assertEqual(listsubnetsresponse.status_code, 200)
        self.assertNotIn('None', listSubnetName)
        print(" ")

        print('->>>>>>> test Neutron List Subnets By Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets?name=" + listSubnetName
        listsubnetByNameresponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetByNameresponse.status_code, 200)
        self.assertNotIn('None', json.loads(
            listsubnetByNameresponse.content)["subnets"][0]["name"])
        print(" ")

        print('->>>>>>> test Neutron List Subnets By Id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets?id=" + listSubnetId
        listsubnetsbyidresponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetsbyidresponse.status_code, 200)
        self.assertNotIn("None", json.loads(
            listsubnetsbyidresponse.content)["subnets"][0]["name"])
        print(" ")

        print('->>>>>>> test Neutron List Subnets By Multiple Id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets?id=" + \
            listSubnetId + "&id=" + listSubnetId2
        listsubnetsbymultipleidsresponse = requests.get(url, headers=headers)
        self.assertEqual(listsubnetsbymultipleidsresponse.status_code, 200)
        self.assertNotIn("None", json.loads(
            listsubnetsbymultipleidsresponse.content)["subnets"][0]["name"])
        print(" ")

        print('->>>>>>> test Neutron Show Subnet->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets/%s" % (
            json.loads(listsubnetsresponse.content)["subnets"][0]["id"])
        showsubnetsresponse = requests.get(url, headers=headers)
        self.assertEqual(showsubnetsresponse.status_code, 200)
        self.assertNotIn("None", json.loads(
            showsubnetsresponse.content)["subnet"]["name"])
        print(" ")

        print('->>>>>>> test Neutron Show Non-Existing Subnet->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets/non-existing-id123"
        showsubnetsresponse = requests.get(url, headers=headers)
        self.assertEqual(showsubnetsresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Create Subnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets"
        createsubnetdata = '{"subnet": {"name": "new_subnet", "network_id": "%s","ip_version": 4,"cidr": "10.0.0.1/24"} }' % (
            json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetresponse = requests.post(
            url, data=createsubnetdata, headers=headers)
        self.assertEqual(createsubnetresponse.status_code, 201)
        self.assertEqual(json.loads(createsubnetresponse.content)[
                         "subnet"]["name"], "new_subnet")
        print(" ")

        print('->>>>>>> test Neutron Create Second Subnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets"
        createsubnetdata = '{"subnet": {"name": "new_subnet", "network_id": "%s","ip_version": 4,"cidr": "10.0.0.1/24"} }' % (
            json.loads(createnetworkresponse.content)["network"]["id"])
        createsubnetfailureresponse = requests.post(
            url, data=createsubnetdata, headers=headers)
        self.assertEqual(createsubnetfailureresponse.status_code, 409)
        print(" ")

        print('->>>>>>> test Neutron Update Subnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets/%s" % (
            json.loads(createsubnetresponse.content)["subnet"]["id"])
        updatesubnetdata = '{"subnet": {"name": "new_subnet_new_name", "network_id":"some_id", "tenant_id":"new_tenant_id", "allocation_pools":"change_me", "gateway_ip":"192.168.1.120", "ip_version":4, "cidr":"10.0.0.1/24", "id":"some_new_id", "enable_dhcp":true} }'
        updatesubnetresponse = requests.put(
            url, data=updatesubnetdata, headers=headers)
        self.assertEqual(updatesubnetresponse.status_code, 200)
        self.assertEqual(json.loads(updatesubnetresponse.content)[
                         "subnet"]["name"], "new_subnet_new_name")
        print(" ")

        print('->>>>>>> test Neutron Update Non-Existing Subnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/subnets/non-existing-subnet-12345"
        updatenonexistingsubnetdata = '{"subnet": {"name": "new_subnet_new_name"} }'
        updatenonexistingsubnetresponse = requests.put(
            url, data=updatenonexistingsubnetdata, headers=headers)
        self.assertEqual(updatenonexistingsubnetresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron List Ports ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports"
        listportsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsesponse.status_code, 200)
        self.assertEqual(json.loads(listportsesponse.content)
                         ["ports"][0]["status"], "ACTIVE")
        listPortsName = json.loads(listportsesponse.content)[
            "ports"][0]["name"]
        listPortsId1 = json.loads(listportsesponse.content)["ports"][0]["id"]
        listPortsId2 = json.loads(listportsesponse.content)["ports"][1]["id"]
        print(" ")

        print('->>>>>>> test Neutron List Ports By Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports?name=" + listPortsName
        listportsbynameesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbynameesponse.status_code, 200)
        self.assertEqual(json.loads(listportsbynameesponse.content)[
                         "ports"][0]["name"], listPortsName)
        print(" ")

        print('->>>>>>> test Neutron List Ports By Id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports?id=" + listPortsId1
        listportsbyidesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbyidesponse.status_code, 200)
        self.assertEqual(json.loads(listportsbyidesponse.content)[
                         "ports"][0]["id"], listPortsId1)
        print(" ")

        print('->>>>>>> test Neutron List Ports By Multiple Ids ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports?id=" + \
            listPortsId1 + "&id=" + listPortsId2
        listportsbymultipleidsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbymultipleidsesponse.status_code, 200)
        self.assertEqual(json.loads(listportsbymultipleidsesponse.content)[
                         "ports"][0]["id"], listPortsId1)
        print(" ")

        print('->>>>>>> test Neutron List Ports By Device ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        server_url = "http://0.0.0.0:18774/v2.1/id_bla/servers/firewall1:9df6a98f-9e11-4cb7-b3c0-InAdUnitTest"
        server_response = requests.get(server_url, headers=headers)
        firewall1_server = json.loads(server_response.content)["server"]
        device_id = firewall1_server["id"]
        url = "http://0.0.0.0:19696/v2.0/ports?device_id=%s" % device_id
        list_ports_by_device_id_response = requests.get(url, headers=headers)
        self.assertEqual(list_ports_by_device_id_response.status_code, 200)
        list_ports_by_device_id_ports = json.loads(list_ports_by_device_id_response.content)["ports"]

        self.assertTrue(any(list_ports_by_device_id_ports), "Expected at least one port for device")
        for port in list_ports_by_device_id_ports:
            self.assertTrue(port["name"].startswith("firewall1:"), "Expected all ports to belong to firewall1")
        print(" ")

        print('->>>>>>> test Neutron List Non-Existing Ports ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports?id=non-existing-port-id"
        listportsbynonexistingidsesponse = requests.get(url, headers=headers)
        self.assertEqual(listportsbynonexistingidsesponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Show Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports/%s" % (
            json.loads(listportsesponse.content)["ports"][0]["id"])
        showportresponse = requests.get(url, headers=headers)
        self.assertEqual(showportresponse.status_code, 200)
        self.assertEqual(json.loads(showportresponse.content)
                         ["port"]["status"], "ACTIVE")
        print(" ")

        print('->>>>>>> test Neutron Show Non-Existing Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports/non-existing-portid123"
        shownonexistingportresponse = requests.get(url, headers=headers)
        self.assertEqual(shownonexistingportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Create Port In Non-Existing Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports"
        createnonexistingportdata = '{"port": {"name": "new_port", "network_id": "non-existing-id"} }'
        createnonexistingnetworkportresponse = requests.post(
            url, data=createnonexistingportdata, headers=headers)
        self.assertEqual(createnonexistingnetworkportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Create Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports"
        createportdata = '{"port": {"name": "new_port", "network_id": "%s", "admin_state_up":true, "device_id":"device_id123", "device_owner":"device_owner123", "fixed_ips":"change_me","id":"new_id1234", "mac_address":"12:34:56:78:90", "status":"change_me", "tenant_id":"tenant_id123"} }' % (json.loads(createnetworkresponse.content)[
                                                                                                                                                                                                                                                                                                    "network"]["id"])
        createportresponse = requests.post(
            url, data=createportdata, headers=headers)
        self.assertEqual(createportresponse.status_code, 201)
        print(createportresponse.content)
        createport = json.loads(createportresponse.content)["port"]
        self.assertEqual(createport["name"], "new_port")
        print(" ")

        print('->>>>>>> test Neutron Create Port With Existing Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports"
        network_id = json.loads(createnetworkresponse.content)["network"]["id"]
        createportwithexistingnamedata = '{"port": {"name": "duplicate_port_name", "network_id": "%s"} }' % network_id
        createportwithexistingnameresponse1 = requests.post(
            url, data=createportwithexistingnamedata, headers=headers)
        createportwithexistingnameresponse2 = requests.post(
            url, data=createportwithexistingnamedata, headers=headers)
        createportwithexistingname1 = json.loads(createportwithexistingnameresponse1.content)["port"]
        createportwithexistingname2 = json.loads(createportwithexistingnameresponse2.content)["port"]
        self.assertEqual(createportwithexistingnameresponse1.status_code, 201)
        self.assertEqual(createportwithexistingnameresponse2.status_code, 201)
        self.assertEqual(createportwithexistingname1["name"], "duplicate_port_name")
        self.assertEqual(createportwithexistingname2["name"], "duplicate_port_name")
        self.assertNotEqual(createportwithexistingname1["id"], createportwithexistingname2["id"], "Duplicate port should have different id")
        print(" ")

        print('->>>>>>> test Neutron Create Port Without Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports"
        createportdatawithoutname = '{"port": {"network_id": "%s"} }' % (
            json.loads(createnetworkresponse.content)["network"]["id"])
        createportwithoutnameresponse = requests.post(
            url, data=createportdatawithoutname, headers=headers)
        self.assertEqual(createportwithoutnameresponse.status_code, 201)
        self.assertIn("port:cp", json.loads(
            createportwithoutnameresponse.content)["port"]["name"])
        print(" ")

        print('->>>>>>> test Neutron Update Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(json.loads(createportresponse.content)["port"]["name"])
        url = "http://0.0.0.0:19696/v2.0/ports/%s" % (
            json.loads(createportresponse.content)["port"]["name"])
        updateportdata = '{"port": {"name": "new_port_new_name", "admin_state_up":true, "device_id":"device_id123", "device_owner":"device_owner123", "fixed_ips":"change_me","mac_address":"12:34:56:78:90", "status":"change_me", "tenant_id":"tenant_id123", "network_id":"network_id123"} }'
        updateportresponse = requests.put(
            url, data=updateportdata, headers=headers)
        self.assertEqual(updateportresponse.status_code, 200)
        self.assertEqual(json.loads(updateportresponse.content)[
                         "port"]["name"], "new_port_new_name")
        print(" ")

        print('->>>>>>> test Neutron Update Non-Existing Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/ports/non-existing-port-ip"
        updatenonexistingportdata = '{"port": {"name": "new_port_new_name"} }'
        updatenonexistingportresponse = requests.put(
            url, data=updatenonexistingportdata, headers=headers)
        self.assertEqual(updatenonexistingportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Delete Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        righturl = "http://0.0.0.0:19696/v2.0/ports/%s" % (
            json.loads(createportresponse.content)["port"]["id"])
        deleterightportresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deleterightportresponse.status_code, 204)
        print(" ")

        print('->>>>>>> test Neutron Delete Non-Existing Port ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:19696/v2.0/ports/unknownid"
        deletewrongportresponse = requests.delete(wrongurl, headers=headers)
        self.assertEqual(deletewrongportresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Neutron Delete Subnet ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:19696/v2.0/subnets/unknownid"
        righturl = "http://0.0.0.0:19696/v2.0/subnets/%s" % (
            json.loads(updatesubnetresponse.content)["subnet"]["id"])
        deletewrongsubnetresponse = requests.delete(wrongurl, headers=headers)
        deleterightsubnetresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deletewrongsubnetresponse.status_code, 404)
        self.assertEqual(deleterightsubnetresponse.status_code, 204)
        print(" ")

        print('->>>>>>> test Neutron Delete Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        righturl = "http://0.0.0.0:19696/v2.0/networks/%s" % (
            json.loads(createnetworkresponse.content)["network"]["id"])
        deleterightnetworkresponse = requests.delete(righturl, headers=headers)
        self.assertEqual(deleterightnetworkresponse.status_code, 204)
        print(" ")

        print('->>>>>>> test Neutron Delete Non-Existing Network ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        wrongurl = "http://0.0.0.0:19696/v2.0/networks/unknownid"
        deletewrongnetworkresponse = requests.delete(wrongurl, headers=headers)
        self.assertEqual(deletewrongnetworkresponse.status_code, 404)
        print(" ")

    def testKeystomeDummy(self):
        print('->>>>>>> test Keystone Dummy Class->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(" ")

        headers = {'Content-type': 'application/json'}
        test_heatapi_keystone_get_token = open(os.path.join(os.path.dirname(
            __file__), "templates/test_heatapi_keystone_get_token.yml")).read()

        print('->>>>>>> test Keystone List Versions ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:15000/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionstackresponse.content)[
                         "versions"]["values"][0]["id"], "v2.0")
        print(" ")

        print('->>>>>>> test Keystone Show ApiV2 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:15000/v2.0"
        showapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(showapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(showapiversionstackresponse.content)[
                         "version"]["id"], "v2.0")
        print(" ")

        print('->>>>>>> test Keystone Get Token ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:15000/v2.0/tokens"
        gettokenstackresponse = requests.post(url, data=json.dumps(
            yaml.load(test_heatapi_keystone_get_token)), headers=headers)
        self.assertEqual(gettokenstackresponse.status_code, 200)
        self.assertEqual(json.loads(gettokenstackresponse.content)[
                         "access"]["user"]["name"], "tenantName")
        print(" ")

    def testHeatDummy(self):
        print('->>>>>>> test Heat Dummy Class->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        print(" ")

        headers = {'Content-type': 'application/json'}
        test_heatapi_template_create_stack = open(os.path.join(os.path.dirname(
            __file__), "templates/test_heatapi_template_create_stack.yml")).read()
        test_heatapi_template_update_stack = open(os.path.join(os.path.dirname(
            __file__), "templates/test_heatapi_template_update_stack.yml")).read()

        print('->>>>>>> test Heat List API Versions Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/"
        listapiversionstackresponse = requests.get(url, headers=headers)
        self.assertEqual(listapiversionstackresponse.status_code, 200)
        self.assertEqual(json.loads(listapiversionstackresponse.content)[
                         "versions"][0]["id"], "v1.0")
        print(" ")

        print('->>>>>>> test Create Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123/stacks"
        createstackresponse = requests.post(url, data=json.dumps(
            yaml.load(test_heatapi_template_create_stack)), headers=headers)
        self.assertEqual(createstackresponse.status_code, 201)
        self.assertNotEqual(json.loads(
            createstackresponse.content)["stack"]["id"], "")
        print(" ")

        print('->>>>>>> test Create Stack With Existing Name ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123/stacks"
        createstackwithexistingnameresponse = requests.post(
            url, data='{"stack_name" : "s1"}', headers=headers)
        self.assertEqual(createstackwithexistingnameresponse.status_code, 409)
        print(" ")

        print('->>>>>>> test Create Stack With Unsupported Version ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123/stacks"
        createstackwitheunsupportedversionresponse = requests.post(
            url, data='{"stack_name" : "stackname123", "template" : {"heat_template_version": "2015-04-29"}}', headers=headers)
        self.assertEqual(
            createstackwitheunsupportedversionresponse.status_code, 400)
        print(" ")

        print('->>>>>>> test List Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123/stacks"
        liststackresponse = requests.get(url, headers=headers)
        self.assertEqual(liststackresponse.status_code, 200)
        self.assertEqual(json.loads(liststackresponse.content)[
                         "stacks"][0]["stack_status"], "CREATE_COMPLETE")
        print(" ")

        print('->>>>>>> test Show Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123showStack/stacks/%s" % json.loads(
            createstackresponse.content)['stack']['id']
        liststackdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(liststackdetailsresponse.status_code, 200)
        self.assertEqual(json.loads(liststackdetailsresponse.content)[
                         "stack"]["stack_status"], "CREATE_COMPLETE")
        print(" ")

        print('->>>>>>> test Show Non-Exisitng Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123showStack/stacks/non_exisitng_id123"
        listnonexistingstackdetailsresponse = requests.get(
            url, headers=headers)
        self.assertEqual(listnonexistingstackdetailsresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Update Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123updateStack/stacks/%s" % json.loads(
            createstackresponse.content)['stack']['id']
        updatestackresponse = requests.put(url, data=json.dumps(yaml.load(test_heatapi_template_update_stack)),
                                           headers=headers)
        self.assertEqual(updatestackresponse.status_code, 202)
        liststackdetailsresponse = requests.get(url, headers=headers)
        self.assertEqual(json.loads(liststackdetailsresponse.content)[
                         "stack"]["stack_status"], "UPDATE_COMPLETE")
        print(" ")

        print('->>>>>>> test Update Non-Existing Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123updateStack/stacks/non_existing_id_1234"
        updatenonexistingstackresponse = requests.put(
            url, data={"non": "sense"}, headers=headers)
        self.assertEqual(updatenonexistingstackresponse.status_code, 404)
        print(" ")

        print('->>>>>>> test Delete Stack ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:18004/v1/tenantabc123showStack/stacks/%s" % \
              json.loads(createstackresponse.content)['stack']['id']
        deletestackdetailsresponse = requests.delete(url, headers=headers)
        self.assertEqual(deletestackdetailsresponse.status_code, 204)
        print(" ")

    def testNeutronSFC(self):
        """
        Tests the Neutron Service Function Chaining implementation. As Some functions build up on others, a
        complete environment is created here:

        Ports:              p1, p2, p3, p4
        Port Pairs:         pp1(p1, p2), pp2(p3, p4)
        Port Pair Groups:   ppg1(pp1, pp2)
        Flow Classifiers:   fc1
        Port Chain:         pc1(ppg1, fc1)
        """

        headers = {'Content-type': 'application/json'}

        print('->>>>>>> Create ports p1 - p6 ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        # Get network id
        network_resp = requests.get(
            "http://0.0.0.0:19696/v2.0/networks?name=default", headers=headers)
        self.assertEqual(network_resp.status_code, 200)
        network_id = json.loads(network_resp.content)["networks"][0]["id"]

        port_responses = list(map(lambda name: requests.post("http://0.0.0.0:19696/v2.0/ports",
                                                             data='{"port": {"name": "%s", "network_id": "%s"}}' %
                                                                  (name, network_id),
                                                             headers=headers),
                                  ["p1", "p2", "p3", "p4", "p5", "p6"]))

        for port in port_responses:
            self.assertEqual(port.status_code, 201)

        port_ids = list(map(lambda response: json.loads(response.content)["port"]["id"], port_responses))

        listflavorsresponse = requests.get("http://0.0.0.0:18774/v2.1/id_bla/flavors", headers=headers)
        self.assertEqual(listflavorsresponse.status_code, 200)
        flavors = json.loads(listflavorsresponse.content)["flavors"]
        m1_tiny_flavor = list(filter(lambda flavor: flavor["name"] == "m1.tiny", flavors))[0]

        listimagesdetailsresponse = requests.get("http://0.0.0.0:18774/v2.1/id_bla/images/detail", headers=headers)
        self.assertEqual(listimagesdetailsresponse.status_code, 200)
        images = json.loads(listimagesdetailsresponse.content)["images"]
        ubuntu_image = list(filter(lambda image: image["name"] == "ubuntu:trusty", images))[0]

        server_url = "http://0.0.0.0:18774/v2.1/id_bla/servers"
        server_template = \
            '{"server": {' \
            '"name": "%s",' \
            '"networks": [{"port": "%s"}, {"port": "%s"}],' \
            '"flavorRef": "%s",' \
            '"imageRef": "%s"' \
            '}}'
        server_responses = map(lambda spec: (
            requests.post(server_url,
                          data=server_template % (
                              spec["name"],
                              spec["ingress"],
                              spec["egress"],
                              m1_tiny_flavor["id"],
                              ubuntu_image["id"]
                          ),
                          headers=headers)
        ), [
            {"name": "s1", "ingress": "p1", "egress": "p2"},
            {"name": "s2", "ingress": "p3", "egress": "p4"},
            {"name": "s3", "ingress": "p5", "egress": "p6"},
        ])
        for response in server_responses:
            self.assertEqual(response.status_code, 200)

        print('->>>>>>> test Neutron SFC Port Pair Create ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pairs"
        pp1_resp = requests.post(url, data='{"port_pair": {"name": "pp1", "ingress": "%s", "egress": "%s"}}' % (
            port_ids[0], port_ids[1]), headers=headers)
        self.assertEqual(pp1_resp.status_code, 201)
        pp2_resp = requests.post(url, data='{"port_pair": {"name": "pp2", "ingress": "%s", "egress": "%s"}}' % (
            port_ids[2], port_ids[3]), headers=headers)
        self.assertEqual(pp2_resp.status_code, 201)
        pp3_resp = requests.post(url, data='{"port_pair": {"name": "pp3", "ingress": "%s", "egress": "%s"}}' % (
            port_ids[4], port_ids[5]), headers=headers)
        self.assertEqual(pp3_resp.status_code, 201)

        pp1_id = json.loads(pp1_resp.content)["port_pair"]["id"]
        pp2_id = json.loads(pp2_resp.content)["port_pair"]["id"]
        pp3_id = json.loads(pp3_resp.content)["port_pair"]["id"]

        print('->>>>>>> test Neutron SFC Port Pair Update ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pairs/%s" % pp3_id
        pp3_update_resp = requests.put(
            url, data='{"port_pair": {"description": "port_pair_update"}}', headers=headers)
        self.assertEqual(pp3_update_resp.status_code, 200)
        self.assertEqual(json.loads(pp3_update_resp.content)[
                         "port_pair"]["description"], "port_pair_update")

        print('->>>>>>> test Neutron SFC Port Pair Delete ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pairs/%s" % pp3_id
        pp3_delete_resp = requests.delete(url, headers=headers)
        self.assertEqual(pp3_delete_resp.status_code, 204)

        print('->>>>>>> test Neutron SFC Port Pair List ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pairs"
        pp_list_resp = requests.get(url, headers=headers)
        self.assertEqual(pp_list_resp.status_code, 200)
        pp_list = json.loads(pp_list_resp.content)["port_pairs"]
        # only pp1 and pp2 should be left
        self.assertEqual(len(pp_list), 2)

        print('->>>>>>> test Neutron SFC Port Pair List filtered by id ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pairs?id=%s" % pp_list[0]["id"]
        pp_list_filtered_by_id_resp = requests.get(url, headers=headers)
        pp_list_filtered_by_id = json.loads(pp_list_filtered_by_id_resp.content)["port_pairs"]
        self.assertEqual(pp_list_filtered_by_id_resp.status_code, 200)
        self.assertEqual(len(pp_list_filtered_by_id), 1)
        self.assertEqual(pp_list_filtered_by_id[0], pp_list[0])

        print('->>>>>>> test Neutron SFC Port Pair Show ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pairs/%s" % pp2_id
        pp2_show_resp = requests.get(url, headers=headers)
        self.assertEqual(pp2_show_resp.status_code, 200)
        self.assertEqual(json.loads(pp2_show_resp.content)
                         ["port_pair"]["name"], "pp2")

        print('->>>>>>> test Neutron SFC Port Pair Group Create ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pair_groups"
        ppg1_resp = requests.post(
            url, data='{"port_pair_group": {"name": "ppg1", "port_pairs": ["%s"]}}' % (pp1_id), headers=headers)
        self.assertEqual(ppg1_resp.status_code, 201)
        ppg2_resp = requests.post(
            url, data='{"port_pair_group": {"name": "ppg2", "port_pairs": ["%s"]}}' % (pp2_id), headers=headers)
        self.assertEqual(ppg2_resp.status_code, 201)
        ppg3_resp = requests.post(
            url, data='{"port_pair_group": {"name": "ppg3", "port_pairs": ["%s"]}}' % (pp2_id), headers=headers)
        self.assertEqual(ppg3_resp.status_code, 201)

        ppg1_id = json.loads(ppg1_resp.content)["port_pair_group"]["id"]
        ppg2_id = json.loads(ppg2_resp.content)["port_pair_group"]["id"]
        ppg3_id = json.loads(ppg3_resp.content)["port_pair_group"]["id"]

        print('->>>>>>> test Neutron SFC Port Pair Group Update ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pair_groups/%s" % ppg3_id
        ppg3_update_resp = requests.put(
            url, data='{"port_pair_group": {"description": "port_pair_group_update"}}', headers=headers)
        self.assertEqual(ppg3_update_resp.status_code, 200)
        self.assertEqual(json.loads(ppg3_update_resp.content)[
                         "port_pair_group"]["description"], "port_pair_group_update")

        print('->>>>>>> test Neutron SFC Port Pair Group Delete ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pair_groups/%s" % ppg3_id
        ppg3_delete_resp = requests.delete(url, headers=headers)
        self.assertEqual(ppg3_delete_resp.status_code, 204)

        print('->>>>>>> test Neutron SFC Port Pair Group List ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pair_groups"
        ppg_list_resp = requests.get(url, headers=headers)
        self.assertEqual(ppg_list_resp.status_code, 200)
        # only ppg1 and ppg2 should be left
        self.assertEqual(
            len(json.loads(ppg_list_resp.content)["port_pair_groups"]), 2)

        print('->>>>>>> test Neutron SFC Port Pair Group Show ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_pair_groups/%s" % ppg2_id
        ppg2_show_resp = requests.get(url, headers=headers)
        self.assertEqual(ppg2_show_resp.status_code, 200)
        self.assertEqual(json.loads(ppg2_show_resp.content)[
                         "port_pair_group"]["name"], "ppg2")

        print('->>>>>>> test Neutron SFC Flow Classifier Create ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/flow_classifiers"
        fc1_resp = requests.post(
            url, data='{"flow_classifier": {"name": "fc1", "logical_source_port": "p1", "source_port_range_min": 22, "source_port_range_max": 4000}}', headers=headers)
        self.assertEqual(fc1_resp.status_code, 201)
        fc2_resp = requests.post(
            url, data='{"flow_classifier": {"name": "fc2", "logical_source_port": "p2", "source_port_range_min": 22, "source_port_range_max": 4000}}', headers=headers)
        self.assertEqual(fc2_resp.status_code, 201)

        fc1_id = json.loads(fc1_resp.content)["flow_classifier"]["id"]
        fc2_id = json.loads(fc2_resp.content)["flow_classifier"]["id"]

        print('->>>>>>> test Neutron SFC Flow Classifier Update ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/flow_classifiers/%s" % fc2_id
        fc2_update_resp = requests.put(
            url, data='{"flow_classifier": {"description": "flow_classifier_update"}}', headers=headers)
        self.assertEqual(fc2_update_resp.status_code, 200)
        self.assertEqual(json.loads(fc2_update_resp.content)[
                         "flow_classifier"]["description"], "flow_classifier_update")

        print('->>>>>>> test Neutron SFC Flow Classifier Delete ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/flow_classifiers/%s" % fc2_id
        fc2_delete_resp = requests.delete(url, headers=headers)
        self.assertEqual(fc2_delete_resp.status_code, 204)

        print('->>>>>>> test Neutron SFC Flow Classifier List ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/flow_classifiers"
        fc_list_resp = requests.get(url, headers=headers)
        self.assertEqual(fc_list_resp.status_code, 200)
        self.assertEqual(len(json.loads(fc_list_resp.content)
                             ["flow_classifiers"]), 1)  # only fc1

        print('->>>>>>> test Neutron SFC Flow Classifier Show ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/flow_classifiers/%s" % fc1_id
        fc1_show_resp = requests.get(url, headers=headers)
        self.assertEqual(fc1_show_resp.status_code, 200)
        self.assertEqual(json.loads(fc1_show_resp.content)[
                         "flow_classifier"]["name"], "fc1")

        print('->>>>>>> test Neutron SFC Port Chain Create ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_chains"
        pc1_resp = requests.post(url, data='{"port_chain": {"name": "pc1", "port_pair_groups": ["%s"], "flow_classifiers": ["%s"]}}' % (
            ppg1_id, fc1_id), headers=headers)
        self.assertEqual(pc1_resp.status_code, 201)
        pc2_resp = requests.post(url, data='{"port_chain": {"name": "pc2", "port_pair_groups": ["%s"], "flow_classifiers": ["%s"]}}' % (
            ppg1_id, fc1_id), headers=headers)
        self.assertEqual(pc2_resp.status_code, 201)

        pc1_id = json.loads(pc1_resp.content)["port_chain"]["id"]
        pc2_id = json.loads(pc2_resp.content)["port_chain"]["id"]

        print('->>>>>>> test Neutron SFC Port Chain Update ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_chains/%s" % pc2_id
        pc2_update_resp = requests.put(
            url, data='{"port_chain": {"description": "port_chain_update"}}', headers=headers)
        self.assertEqual(pc2_update_resp.status_code, 200)
        self.assertEqual(json.loads(pc2_update_resp.content)[
                         "port_chain"]["description"], "port_chain_update")

        print('->>>>>>> test Neutron SFC Port Chain Delete ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_chains/%s" % pc2_id
        pc2_delete_resp = requests.delete(url, headers=headers)
        self.assertEqual(pc2_delete_resp.status_code, 204)

        print('->>>>>>> test Neutron SFC Port Chain List ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_chains"
        pc_list_resp = requests.get(url, headers=headers)
        self.assertEqual(pc_list_resp.status_code, 200)
        self.assertEqual(len(json.loads(pc_list_resp.content)
                             ["port_chains"]), 1)  # only pc1

        print('->>>>>>> test Neutron SFC Port Chain Show ->>>>>>>>>>>>>>>')
        print('->>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>')
        url = "http://0.0.0.0:19696/v2.0/sfc/port_chains/%s" % pc1_id
        pc1_show_resp = requests.get(url, headers=headers)
        self.assertEqual(pc1_show_resp.status_code, 200)
        self.assertEqual(json.loads(pc1_show_resp.content)
                         ["port_chain"]["name"], "pc1")


if __name__ == '__main__':
    unittest.main()
