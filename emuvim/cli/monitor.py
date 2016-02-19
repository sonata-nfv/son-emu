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

    def get_rate(self, args):
        r = self.c.monitor_get_rate(
            args.get("vnf_name"),
            args.get("direction"))
        pp.pprint(r)


parser = argparse.ArgumentParser(description='son-emu network')
parser.add_argument(
    "command",
    help="Action to be executed: get_rate")
parser.add_argument(
    "--vnf_name", "-vnf", dest="vnf_name",
    help="vnf name to be monitored")
parser.add_argument(
    "--direction", "-d", dest="direction",
    help="in (ingress rate) or out (egress rate)")

def main(argv):
    print "This is the son-emu monitor CLI."
    print "Arguments: %s" % str(argv)
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
