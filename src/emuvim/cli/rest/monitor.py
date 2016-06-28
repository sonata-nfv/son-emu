from requests import get, put, delete
from tabulate import tabulate
import pprint
import argparse
import json
from emuvim.cli import prometheus

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

    def setup_metric(self, args):
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        vnf_interface = self._parse_vnf_interface(args.get("vnf_name"))

        response = put("%s/restapi/monitor/%s/%s/%s" %
                       (args.get("endpoint"),
                        vnf_name,
                        vnf_interface,
                        args.get("metric")))
        pp.pprint(response.json())

    def stop_metric(self, args):
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        vnf_interface = self._parse_vnf_interface(args.get("vnf_name"))

        response = delete("%s/restapi/monitor/%s/%s/%s" %
                       (args.get("endpoint"),
                        vnf_name,
                        vnf_interface,
                        args.get("metric")))
        pp.pprint(response.json())

    def setup_flow(self, args):
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        vnf_interface = self._parse_vnf_interface(args.get("vnf_name"))

        response = put("%s/restapi/monitor/%s/%s/%s/%s" %
                       (args.get("endpoint"),
                        vnf_name,
                        vnf_interface,
                        args.get("metric"),
                        args.get("cookie")))

        pp.pprint(response.json())

    def stop_flow(self, args):
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        vnf_interface = self._parse_vnf_interface(args.get("vnf_name"))

        response = delete("%s/restapi/monitor/%s/%s/%s/%s" %
                       (args.get("endpoint"),
                        vnf_name,
                        vnf_interface,
                        args.get("metric"),
                        args.get("cookie")))

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

parser = argparse.ArgumentParser(description='son-emu monitor')
parser.add_argument(
    "command",
    choices=['setup_metric', 'stop_metric', 'setup_flow', 'stop_flow','prometheus'],
    help="setup/stop a metric/flow to be monitored or query Prometheus")
parser.add_argument(
    "--vnf_name", "-vnf", dest="vnf_name",
    help="vnf name:interface to be monitored")
parser.add_argument(
    "--metric", "-m", dest="metric",
    help="tx_bytes, rx_bytes, tx_packets, rx_packets")
parser.add_argument(
    "--cookie", "-c", dest="cookie",
    help="flow cookie to monitor")
parser.add_argument(
    "--query", "-q", dest="query",
    help="prometheus query")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center where the vnf is deployed")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5000",
    help="UUID of the plugin to be manipulated.")

def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)