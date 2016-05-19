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
        self.c = zerorpc.Client(heartbeat=None, timeout=120) #heartbeat=None, timeout=120
        self.c.connect("tcp://127.0.0.1:4242")  # TODO hard coded for now. we'll change this later
        self.cmds = {}

    def execute_command(self, args):
        if getattr(self, args["command"]) is not None:
            # call the local method with the same name as the command arg
            getattr(self, args["command"])(args)
        else:
            print("Command not implemented.")

    def start(self, args):
        nw_list = list()
        if args.get("network") is not None:
            nw_list = self._parse_network(args.get("network"))
        r = self.c.compute_action_start(
            args.get("datacenter"),
            args.get("name"),
            args.get("image"),
            nw_list,
            args.get("docker_command")
            )
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
                    eth0ip = status.get("network")[0].get("ip")
                    eth0status = "up" if status.get(
                        "network")[0].get("up") else "down"
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
        print(tabulate(table, headers=headers, tablefmt="grid"))

    def status(self, args):
        r = self.c.compute_status(
            args.get("datacenter"), args.get("name"))
        pp.pprint(r)

    def profile(self, args):
        nw_list = list()
        if args.get("network") is not None:
            nw_list = self._parse_network(args.get("network"))

        params = self._create_dict(
            network=nw_list,
            command=args.get("docker_command"),
            input=args.get("input"),
            output=args.get("output"))

        for output in self.c.compute_profile(
            args.get("datacenter"),
            args.get("name"),
            args.get("image"),
            params
            ):
            print(output + '\n')

        #pp.pprint(r)
        #print(r)

    def _create_dict(self, **kwargs):
        return kwargs

    def _parse_network(self, network_str):
        '''
        parse the options for all network interfaces of the vnf
        :param network_str: (id=x,ip=x.x.x.x/x), ...
        :return: list of dicts [{"id":x,"ip":"x.x.x.x/x"}, ...]
        '''
        nw_list = list()
        networks = network_str[1:-1].split('),(')
        for nw in networks:
            nw_dict = dict(tuple(e.split('=')) for e in nw.split(','))
            nw_list.append(nw_dict)

        return nw_list



parser = argparse.ArgumentParser(description='son-emu compute')
parser.add_argument(
    "command",
    choices=['start', 'stop', 'list', 'status', 'profile'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to in which the compute instance should be executed")
parser.add_argument(
    "--name", "-n", dest="name",
    help="Name of compute instance e.g. 'vnf1'")
parser.add_argument(
    "--image","-i", dest="image",
    help="Name of container image to be used e.g. 'ubuntu:trusty'")
parser.add_argument(
    "--dcmd", "-c", dest="docker_command",
    help="Startup command of the container e.g. './start.sh'")
parser.add_argument(
    "--net", dest="network",
    help="Network properties of a compute instance e.g. \
          '(id=input,ip=10.0.10.3/24),(id=output,ip=10.0.10.4/24)' for multiple interfaces.")
parser.add_argument(
    "--input", "-in", dest="input",
    help="input interface of the vnf to profile")
parser.add_argument(
    "--output", "-out", dest="output",
    help="output interface of the vnf to profile")


def main(argv):
    args = vars(parser.parse_args(argv))
    c = ZeroRpcClient()
    c.execute_command(args)
