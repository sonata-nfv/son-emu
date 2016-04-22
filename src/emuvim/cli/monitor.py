"""
son-emu monitor CLI
(c) 2016 by Manuel Peuster <manuel.peuster@upb.de>
"""

import argparse
import pprint
from tabulate import tabulate
import zerorpc
import time


pp = pprint.PrettyPrinter(indent=4)

class ZeroRpcClient(object):

    def __init__(self):
        self.c = zerorpc.Client()
        # TODO connect to DCNetwork API
        #self.c.connect("tcp://127.0.0.1:4242")  # TODO hard coded for now. we'll change this later
        self.c.connect("tcp://127.0.0.1:5151")
        self.cmds = {}

    def execute_command(self, args):
        if getattr(self, args["command"]) is not None:
            # call the local method with the same name as the command arg
            getattr(self, args["command"])(args)
        else:
            print "Command not implemented."

    def setup_metric(self, args):
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        vnf_interface = self._parse_vnf_interface(args.get("vnf_name"))
        r = self.c.setup_metric(
            vnf_name,
            vnf_interface,
            args.get("metric"))
        pp.pprint(r)

    def stop_metric(self, args):
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        vnf_interface = self._parse_vnf_interface(args.get("vnf_name"))
        r = self.c.stop_metric(
            vnf_name,
            vnf_interface,
            args.get("metric"))
        pp.pprint(r)

    def _parse_vnf_name(self, vnf_name_str):
        vnf_name = vnf_name_str.split(':')[0]
        return vnf_name

    def _parse_vnf_interface(self, vnf_name_str):
        try:
            vnf_interface = vnf_name_str.split(':')[1]
        except:
            vnf_interface = None

        return vnf_interface

parser = argparse.ArgumentParser(description='son-emu network')
parser.add_argument(
    "command",
    help="Action to be executed")
parser.add_argument(
    "--vnf_name", "-vnf", dest="vnf_name",
    help="vnf name:interface to be monitored")
parser.add_argument(
    "--metric", "-m", dest="metric",
    help="tx_bytes, rx_bytes, tx_packets, rx_packets")

def main(argv):
    #print "This is the son-emu monitor CLI."
    #print "Arguments: %s" % str(argv)
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
