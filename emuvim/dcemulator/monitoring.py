__author__ = 'Administrator'

import urllib2
import logging
from mininet.node import  OVSSwitch
import ast
logging.basicConfig(level=logging.INFO)

"""
class to read openflow stats from the Ryu controller of the DCNEtwork
"""

class DCNetworkMonitor():
    def __init__(self, net):
        self.net = net
        # link to REST_API
        self.ip = '0.0.0.0'
        self.port = '8080'
        self.REST_api = 'http://{0}:{1}'.format(self.ip,self.port)


    def get_rate(self, vnf_name, direction='tx'):
        try:
            vnf_switch = self.net.DCNetwork_graph.neighbors(str(vnf_name))

            if len(vnf_switch) > 1:
                logging.info("vnf: {0} has multiple ports".format(vnf_name))
                return
            elif len(vnf_switch) == 0:
                logging.info("vnf: {0} is not connected".format(vnf_name))
                return
            else:
                vnf_switch = vnf_switch[0]
            next_node = self.net.getNodeByName(vnf_switch)

            if not isinstance( next_node, OVSSwitch ):
                logging.info("vnf: {0} is not connected to switch".format(vnf_name))
                return

            mon_port = self.net.DCNetwork_graph[vnf_name][vnf_switch]['dst_port']
            switch_dpid = x = int(str(next_node.dpid),16)

            ret = self.REST_cmd('stats/port', switch_dpid)
            port_stat_dict = ast.literal_eval(ret)
            for port_stat in port_stat_dict[str(switch_dpid)]:
                if port_stat['port_no'] == mon_port:
                    return port_stat
                    break

            return ret

        except Exception as ex:
            logging.exception("get_txrate error.")
            return ex.message



    def REST_cmd(self, prefix, dpid):
        url = self.REST_api + '/' + str(prefix) + '/' + str(dpid)
        req = urllib2.Request(url)
        ret = urllib2.urlopen(req).read()
        return ret