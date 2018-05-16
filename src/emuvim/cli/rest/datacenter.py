# Copyright (c) 2015 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
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

    def list(self, args):
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
        print(tabulate(table, headers=headers, tablefmt="grid"))

    def status(self, args):
        list = get('%s/restapi/datacenter/%s' %
                   (args.get("endpoint"), args.get("datacenter"))).json()
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

        print(tabulate(table, headers=headers, tablefmt="grid"))


parser = argparse.ArgumentParser(description='son-emu-cli datacenter')
parser.add_argument(
    "command",
    choices=['list', 'status'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to which the command should be applied.")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5001",
    help="REST API endpoint of son-emu (default:http://127.0.0.1:5001)")


def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)
