from requests import get,put
from tabulate import tabulate
import pprint
import argparse
import json

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

    def start(self, args):

        nw_list = list()
        if args.get("network") is not None:
            nw_list = self._parse_network(args.get("network"))
        req = {'image':args.get("image"),
               'command':args.get("docker_command"),
               'network':nw_list}

        response = put("%s/restapi/compute/%s/%s/start" %
                       (args.get("endpoint"),
                        args.get("datacenter"),
                        args.get("name")),
                       json = json.dumps(req))
        pp.pprint(response.json())

    def stop(self, args):

        response = get("%s/restapi/compute/%s/%s/stop" %
                       (args.get("endpoint"),
                        args.get("datacenter"),
                        args.get("name")))
        pp.pprint(response.json())

    def list(self,args):

        list = get('%s/restapi/compute/%s' % (args.get("endpoint"),args.get('datacenter'))).json()

        table = []
        for c in list:
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

    def status(self,args):

        list = get("%s/restapi/compute/%s/%s" %
                   (args.get("endpoint"),
                    args.get("datacenter"),
                    args.get("name"))).json()
        pp.pprint(list)



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


parser = argparse.ArgumentParser(description='son-emu datacenter')
parser.add_argument(
    "command",
    choices=['start', 'stop', 'list', 'status'],
    help="Action to be executed.")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center to which the command should be applied.")
parser.add_argument(
    "--name", "-n", dest="name",
    help="Name of compute instance e.g. 'vnf1'.")
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
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5001",
    help="UUID of the plugin to be manipulated.")

def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)