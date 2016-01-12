"""
son-emu compute CLI
"""

import argparse
import pprint
import zerorpc


pp = pprint.PrettyPrinter(indent=4)


class ZeroRpcClient(object):

    def __init__(self):
        self.c = zerorpc.Client()
        self.c.connect("tcp://127.0.0.1:4242")  # yes, hard coded for now. we'll change this later
        self.cmds = {}

    def execute_command(self, args):
        if getattr(self, args["command"]) is not None:
            # call the local method with the same name as the command arg
            getattr(self, args["command"])(args)
        else:
            print "Command not implemented."

    def start(self, args):
        r = self.c.compute_action_start(
            args.get("datacenter"), args.get("name"))
        pp.pprint(r)

    def stop(self, args):
        r = self.c.compute_action_stop(
            args.get("datacenter"), args.get("name"))
        pp.pprint(r)

    def list(self, args):
        print "TODO: Not implemented"

    def status(self, args):
        print "TODO: Not implemented"


parser = argparse.ArgumentParser(description='son-emu compute')
parser.add_argument("command", help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter", help="Data center.")
parser.add_argument(
    "--name", "-n", dest="name", help="Compute name.")
# TODO: IP, image, etc. pp.


def main(argv):
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
