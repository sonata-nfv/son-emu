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
from requests import get, put
import pprint
import argparse
from emuvim.cli import prometheus

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

    def setup_metric(self, args):

        params = self._create_dict(
            vnf_name=self._parse_vnf_name(args.get("vnf_name")),
            vnf_interface=self._parse_vnf_interface(args.get("vnf_name")),
            metric=args.get("metric"))

        url = "{0}/restapi/monitor/interface".format(args.get("endpoint"))
        response = put(url, params=params)
        pp.pprint(response.text)

    def stop_metric(self, args):
        params = self._create_dict(
            vnf_name=self._parse_vnf_name(args.get("vnf_name")),
            vnf_interface=self._parse_vnf_interface(args.get("vnf_name")),
            metric=args.get("metric"))

        url = "{0}/restapi/monitor/interface".format(args.get("endpoint"))
        response = put(url, params=params)
        pp.pprint(response.text)

    def setup_flow(self, args):
        params = self._create_dict(
            vnf_name=self._parse_vnf_name(args.get("vnf_name")),
            vnf_interface=self._parse_vnf_interface(args.get("vnf_name")),
            metric=args.get("metric"),
            cookie=args.get("cookie"))

        url = "{0}/restapi/monitor/flow".format(args.get("endpoint"))
        response = put(url, params=params)
        pp.pprint(response.text)

    def stop_flow(self, args):
        params = self._create_dict(
            vnf_name=self._parse_vnf_name(args.get("vnf_name")),
            vnf_interface=self._parse_vnf_interface(args.get("vnf_name")),
            metric=args.get("metric"),
            cookie=args.get("cookie"))

        url = "{0}/restapi/monitor/flow".format(args.get("endpoint"))
        response = put(url, params=params)
        pp.pprint(response.text)

    def prometheus(self, args):
        # This functions makes it more user-friendly to create the correct prometheus query
        # <uuid> is replaced by the correct uuid of the deployed vnf container
        vnf_name = self._parse_vnf_name(args.get("vnf_name"))
        query = args.get("query")

        vnf_status = get("%s/restapi/compute/%s/%s" %
                         (args.get("endpoint"),
                          args.get("datacenter"),
                             vnf_name)).json()
        uuid = vnf_status['id']
        query = query.replace('<uuid>', uuid)

        response = prometheus.query_Prometheus(query)
        pp.pprint(response)

    def _parse_vnf_name(self, vnf_name_str):
        vnf_name = vnf_name_str.split(':')[0]
        return vnf_name

    def _parse_vnf_interface(self, vnf_name_str):
        try:
            vnf_interface = vnf_name_str.split(':')[1]
        except BaseException:
            vnf_interface = None

        return vnf_interface

    def _create_dict(self, **kwargs):
        return kwargs


parser = argparse.ArgumentParser(description='son-emu-cli monitor')
parser.add_argument(
    "command",
    choices=['setup_metric', 'stop_metric',
             'setup_flow', 'stop_flow', 'prometheus'],
    help="setup/stop a metric/flow to be monitored or query Prometheus")
parser.add_argument(
    "--vnf_name", "-vnf", dest="vnf_name",
    help="vnf name:interface to be monitored")
parser.add_argument(
    "--metric", "-m", dest="metric",
    help="tx_bytes, rx_bytes, tx_packets, rx_packets")
parser.add_argument(
    "--cookie", "-c", dest="cookie",
    help="flow cookie to monitor")
parser.add_argument(
    "--query", "-q", dest="query",
    help="prometheus query")
parser.add_argument(
    "--datacenter", "-d", dest="datacenter",
    help="Data center where the vnf is deployed")
parser.add_argument(
    "--endpoint", "-e", dest="endpoint",
    default="http://127.0.0.1:5001",
    help="REST API endpoint of son-emu (default:http://127.0.0.1:5001)")


def main(argv):
    args = vars(parser.parse_args(argv))
    c = RestApiClient()
    c.execute_command(args)
