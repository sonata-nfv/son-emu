"""
son-emu network CLI
(c) 2016 by Manuel Peuster <manuel.peuster@upb.de>
"""

import argparse
import pprint
from tabulate import tabulate
import zerorpc


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

        # note zerorpc does not support named arguments
        r = self.c.network_action_start(
            #args.get("datacenter"),
            vnf_src_name,
            vnf_dst_name,
            params)
        pp.pprint(r)

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

        r = self.c.network_action_stop(
            #args.get("datacenter"),
            vnf_src_name,
            vnf_dst_name,
            params)
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

    def _create_dict(self, **kwargs):
        return kwargs

parser = argparse.ArgumentParser(description='son-emu network')
parser.add_argument(
    "command",
    help="Action to be executed: add|remove")
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
    help="add/remove the flow entries in 2 directions")
parser.add_argument(
    "--cookie", "-c", dest="cookie",
    help="cookie for this flow")

def main(argv):
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
