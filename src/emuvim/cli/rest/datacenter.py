from requests import get
from tabulate import tabulate
import pprint
import argparse

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

    def list(self,args):
        list = get('%s/restapi/datacenter' % args.get('endpoint')).json()
        table = []
        for d in list:
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
        print (tabulate(table, headers=headers, tablefmt="grid"))

    def status(self,args):
        list = get('%s/restapi/datacenter/%s' % ( args.get("endpoint"), args.get("datacenter"))).json()
        table = []
        table.append([list.get('label'),
                  list.get('internalname'),
                  list.get('switch'),
                  list.get('n_running_containers'),
                  len(list.get('metadata'))])

        headers = ["Label",
               "Internal Name",
               "Switch",
               "# Containers",
               "# Metadata Items"]

        print (tabulate(table, headers=headers, tablefmt="grid"))


parser = argparse.ArgumentParser(description='son-emu datacenter')
parser.add_argument(
    "command",
    choices=['list', 'status'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to which the command should be applied.")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5000",
    help="UUID of the plugin to be manipulated.")


def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)

