from requests import get,put, delete
from tabulate import tabulate
import pprint
import argparse
import json

pp = pprint.PrettyPrinter(indent=4)

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
        vnf_src_name = self._parse_vnf_name(args.get("source"))
        vnf_dst_name = self._parse_vnf_name(args.get("destination"))

        params = self._create_dict(
            vnf_src_interface=self._parse_vnf_interface(args.get("source")),
            vnf_dst_interface=self._parse_vnf_interface(args.get("destination")),
            weight=args.get("weight"),
            match=args.get("match"),
            bidirectional=args.get("bidirectional"),
            cookie=args.get("cookie"))

        response = put("%s/restapi/network/%s/%s" %
                       (args.get("endpoint"),
                        vnf_src_name,
                        vnf_dst_name),
                       json=json.dumps(params))
        pp.pprint(response.json())

    def remove(self, args):
        vnf_src_name = self._parse_vnf_name(args.get("source"))
        vnf_dst_name = self._parse_vnf_name(args.get("destination"))

        params = self._create_dict(
            vnf_src_interface=self._parse_vnf_interface(args.get("source")),
            vnf_dst_interface=self._parse_vnf_interface(args.get("destination")),
            weight=args.get("weight"),
            match=args.get("match"),
            bidirectional=args.get("bidirectional"),
            cookie=args.get("cookie"))

        response = delete("%s/restapi/network/%s/%s" %
                       (args.get("endpoint"),
                        vnf_src_name,
                        vnf_dst_name),
                       json=json.dumps(params))
        pp.pprint(response.json())

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

parser = argparse.ArgumentParser(description='son-emu network')
parser.add_argument(
    "command",
    choices=['add', 'remove'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to in which the network action should be initiated")
parser.add_argument(
    "--source", "-src", dest="source",
    help="vnf name of the source of the chain")
parser.add_argument(
    "--destination", "-dst", dest="destination",
    help="vnf name of the destination of the chain")
parser.add_argument(
    "--weight", "-w", dest="weight",
    help="weight metric to calculate the path")
parser.add_argument(
    "--match", "-m", dest="match",
    help="string holding extra matches for the flow entries")
parser.add_argument(
    "--bidirectional", "-b", dest="bidirectional",
    action='store_true',
    help="add/remove the flow entries from src to dst and back")
parser.add_argument(
    "--cookie", "-c", dest="cookie",
    help="cookie for this flow, as easy to use identifier (eg. per tenant/service)")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5000",
    help="UUID of the plugin to be manipulated.")

def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)