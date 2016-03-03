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
        r = self.c.network_action_start(
            #args.get("datacenter"),
            args.get("source"),
            args.get("destination"))
        pp.pprint(r)

    def remove(self, args):
        r = self.c.network_action_stop(
            #args.get("datacenter"),
            args.get("source"),
            args.get("destination"))
        pp.pprint(r)


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

def main(argv):
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
