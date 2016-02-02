"""
son-emu compute CLI
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
            print "Command not implemented."

    def start(self, args):
        network = {}
        if args.get("network") is not None:
            network = {"ip": args.get("network")}
        r = self.c.compute_action_start(
            args.get("datacenter"),
            args.get("name"),
            args.get("image"),
            network)
        pp.pprint(r)

    def stop(self, args):
        r = self.c.compute_action_stop(
            args.get("datacenter"), args.get("name"))
        pp.pprint(r)

    def list(self, args):
        r = self.c.compute_list(
            args.get("datacenter"))
        table = []
        for c in r:
            # for each container add a line to the output table
            if len(c) > 1:
                name = c[0]
                status = c[1]
                eth0ip = None
                eth0status = "down"
                if len(status.get("network")) > 0:
                    eth0ip = status.get("network")[0][1]
                    eth0status = "up" if status.get(
                        "network")[0][3] else "down"
                table.append([status.get("datacenter"),
                              name,
                              status.get("image"),
                              eth0ip,
                              eth0status,
                              status.get("state").get("Status")])
        headers = ["Datacenter",
                   "Container",
                   "Image",
                   "eth0 IP",
                   "eth0 status",
                   "Status"]
        print tabulate(table, headers=headers, tablefmt="grid")

    def status(self, args):
        r = self.c.compute_status(
            args.get("datacenter"), args.get("name"))
        pp.pprint(r)


parser = argparse.ArgumentParser(description='son-emu compute')
parser.add_argument(
    "command",
    help="Action to be executed: start|stop|list")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to in which the compute instance should be executed")
parser.add_argument(
    "--name", "-n", dest="name",
    help="Name of compute instance e.g. 'vnf1'")
parser.add_argument(
    "--image", dest="image",
    help="Name of container image to be used e.g. 'ubuntu'")
parser.add_argument(
    "--net", dest="network",
    help="Network properties of compute instance e.g. '10.0.0.123/8'")


def main(argv):
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
