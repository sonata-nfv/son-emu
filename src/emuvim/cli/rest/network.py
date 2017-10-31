"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
from requests import get,put, delete
import argparse


class RestApiClient():

    def __init__(self):
        self.cmds = {}

    def execute_command(self, args):
        if getattr(self, args["command"]) is not None:
            # call the local method with the same name as the command arg
            getattr(self, args["command"])(args)
        else:
            print("Command not implemented.")

    def add(self, args):
        params = self._create_dict(
            vnf_src_name=self._parse_vnf_name(args.get("source")),
            vnf_dst_name = self._parse_vnf_name(args.get("destination")),
            vnf_src_interface=self._parse_vnf_interface(args.get("source")),
            vnf_dst_interface=self._parse_vnf_interface(args.get("destination")),
            weight=args.get("weight"),
            match=args.get("match"),
            bidirectional=args.get("bidirectional"),
            cookie=args.get("cookie"),
            priority=args.get("priority"))

        response = put("{0}/restapi/network".format(args.get("endpoint")),
                       params=params)
        print(self._nice_print(response.text))

    def remove(self, args):
        params = self._create_dict(
            vnf_src_name = self._parse_vnf_name(args.get("source")),
            vnf_dst_name = self._parse_vnf_name(args.get("destination")),
            vnf_src_interface=self._parse_vnf_interface(args.get("source")),
            vnf_dst_interface=self._parse_vnf_interface(args.get("destination")),
            weight=args.get("weight"),
            match=args.get("match"),
            bidirectional=args.get("bidirectional"),
            cookie=args.get("cookie"),
            priority=args.get("priority"))

        response = delete("{0}/restapi/network".format(args.get("endpoint")),
                          params=params)
        print(self._nice_print(response.text))

    def addLAN(self, args):
        params = self._create_dict(
            vnf_name=self._parse_vnf_name(args.get("source")),
            vnf_interface=self._parse_vnf_interface(args.get("source")),
            vlan_tag=args.get("vlan"))

        response = put("{0}/restapi/networkLAN".format(args.get("endpoint")),
                       params=params)
        print(self._nice_print(response.text))

    def removeLAN(self, args):
        params = self._create_dict(
            vnf_src_name=self._parse_vnf_name(args.get("source")),
            vnf_src_interface=self._parse_vnf_interface(args.get("source")),
            vlan=args.get("vlan"))

        response = delete("{0}/restapi/networkLAN".format(args.get("endpoint")),
                       params=params)
        print(self._nice_print(response.text))

    def _parse_vnf_name(self, vnf_name_str):
        vnf_name = vnf_name_str.split(':')[0]
        return vnf_name

    def _parse_vnf_interface(self, vnf_name_str):
        try:
            vnf_interface = vnf_name_str.split(':')[1]
        except:
            vnf_interface = None

        return vnf_interface

    def _create_dict(self, **kwargs):
        return kwargs

    def _nice_print(self, text):
        # some modules seem to return unicode strings where newlines, other special characters are escaped
        text = str(text).replace('\\n', '\n')
        text = str(text).replace('\\"', '"')
        return text

parser = argparse.ArgumentParser(description='son-emu-cli network')
parser.add_argument(
    "command",
    choices=['add', 'remove', 'addLAN', 'removeLAN'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to in which the network action should be initiated")
parser.add_argument(
    "--source", "-src", dest="source",
    help="vnf name:interface of the source of the chain")
parser.add_argument(
    "--destination", "-dst", dest="destination",
    help="vnf name:interface of the destination of the chain")
parser.add_argument(
    "--weight", "-w", dest="weight",
    help="weight edge attribute to calculate the path")
parser.add_argument(
    "--priority", "-p", dest="priority", default="1000",
    help="priority of flow rule")
parser.add_argument(
    "--match", "-m", dest="match",
    help="string holding extra matches for the flow entries")
parser.add_argument(
    "--bidirectional", "-b", dest="bidirectional", action='store_true',
    help="add/remove the flow entries from src to dst and back")
parser.add_argument(
    "--cookie", "-c", dest="cookie", default="10",
    help="cookie for this flow, as easy to use identifier (eg. per tenant/service)")
parser.add_argument(
    "--vlan", "-vl", dest="vlan",
    help="vlan tag to be used with the specified LAN interface")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5001",
    help="REST API endpoint of son-emu (default:http://127.0.0.1:5001)")

def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)
