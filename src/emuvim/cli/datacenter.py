"""
son-emu datacenter CLI
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
        self.c.connect("tcp://127.0.0.1:4242")  # TODO hard coded for now. we'll change this later
        self.cmds = {}

    def execute_command(self, args):
        if getattr(self, args["command"]) is not None:
            # call the local method with the same name as the command arg
            getattr(self, args["command"])(args)
        else:
            print("Command not implemented.")

    def list(self, args):
        r = self.c.datacenter_list()
        table = []
        for d in r:
            # for each dc add a line to the output table
            if len(d) > 0:
                table.append([d.get("label"),
                              d.get("internalname"),
                              d.get("switch"),
                              d.get("n_running_containers"),
                              len(d.get("metadata"))])
        headers = ["Label",
                   "Internal Name",
                   "Switch",
                   "# Containers",
                   "# Metadata Items"]
        print(tabulate(table, headers=headers, tablefmt="grid"))

    def status(self, args):
        r = self.c.datacenter_status(
            args.get("datacenter"))
        pp.pprint(r)


parser = argparse.ArgumentParser(description='son-emu datacenter')
parser.add_argument(
    "command",
    choices=['list', 'status'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to which the command should be applied.")


def main(argv):
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
