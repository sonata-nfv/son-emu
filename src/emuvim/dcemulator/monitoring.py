__author__ = 'Administrator'

import urllib2
import logging
from mininet.node import  OVSSwitch
import ast
import time
from prometheus_client import start_http_server, Summary, Histogram, Gauge, Counter
import threading
from subprocess import Popen
from os import getcwd

logging.basicConfig(level=logging.INFO)

"""
class to read openflow stats from the Ryu controller of the DCNetwork
"""

class DCNetworkMonitor():
    def __init__(self, net):
        self.net = net
        # link to Ryu REST_API
        self.ip = '0.0.0.0'
        self.port = '8080'
        self.REST_api = 'http://{0}:{1}'.format(self.ip,self.port)

        # helper variables to calculate the metrics
        # TODO put these in a list to support multiple metrics simultaneously
        self.switch_dpid = 0
        self.vnf_name = None
        self.vnf_interface = None
        self.previous_measurement = 0
        self.previous_monitor_time = 0
        self.metric_key = None
        self.mon_port = None


        # Start up the server to expose the metrics to Prometheus.
        start_http_server(8000)
        # supported Prometheus metrics
        self.prom_tx_packet_count = Gauge('sonemu_tx_count_packets', 'Total number of packets sent',
                                          ['vnf_name', 'vnf_interface'])
        self.prom_rx_packet_count = Gauge('sonemu_rx_count_packets', 'Total number of packets received',
                                          ['vnf_name', 'vnf_interface'])
        self.prom_tx_byte_count = Gauge('sonemu_tx_count_bytes', 'Total number of bytes sent',
                                        ['vnf_name', 'vnf_interface'])
        self.prom_rx_byte_count = Gauge('sonemu_rx_count_bytes', 'Total number of bytes received',
                                        ['vnf_name', 'vnf_interface'])

        self.prom_metrics={'tx_packets':self.prom_tx_packet_count, 'rx_packets':self.prom_rx_packet_count,
                           'tx_bytes':self.prom_tx_byte_count,'rx_bytes':self.prom_rx_byte_count}

        # list of installed metrics to monitor
        # each entry can contain this data
        '''
        {
        switch_dpid = 0
        vnf_name = None
        vnf_interface = None
        previous_measurement = 0
        previous_monitor_time = 0
        metric_key = None
        mon_port = None
        }
        '''
        self.network_metrics = []

        # start monitoring thread
        self.monitor_thread = threading.Thread(target=self.get_network_metrics)
        self.monitor_thread.start()

        # helper tools
        self.prometheus_process = None
        self.cAdvisor_process = None


    # first set some parameters, before measurement can start
    def setup_metric(self, vnf_name, vnf_interface=None, metric='tx_packets'):

        network_metric = {}

        # check if port is specified (vnf:port)
        if vnf_interface is None:
            # take first interface by default
            connected_sw = self.net.DCNetwork_graph.neighbors(vnf_name)[0]
            link_dict = self.net.DCNetwork_graph[vnf_name][connected_sw]
            vnf_interface = link_dict[0]['src_port_id']

        network_metric['vnf_name'] = vnf_name
        network_metric['vnf_interface'] = vnf_interface
        #self.vnf_name = vnf_name
        #self.vnf_interface = vnf_interface

        for connected_sw in self.net.DCNetwork_graph.neighbors(vnf_name):
            link_dict = self.net.DCNetwork_graph[vnf_name][connected_sw]
            for link in link_dict:
                # logging.info("{0},{1}".format(link_dict[link],vnf_interface))
                if link_dict[link]['src_port_id'] == vnf_interface:
                    # found the right link and connected switch
                    # logging.info("{0},{1}".format(link_dict[link]['src_port_id'], vnf_source_interface))
                    network_metric['mon_port'] = link_dict[link]['dst_port']
                    # self.mon_port = link_dict[link]['dst_port']
                    break

        if 'mon_port' not in network_metric:
            logging.exception("vnf interface {0}:{1} not found!".format(vnf_name,vnf_interface))
            return "vnf interface {0}:{1} not found!".format(vnf_name,vnf_interface)

        try:
            # default port direction to monitor
            if metric is None:
                metric = 'tx_packets'

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

            if not isinstance(next_node, OVSSwitch):
                logging.info("vnf: {0} is not connected to switch".format(vnf_name))
                return

            network_metric['previous_measurement'] = 0
            network_metric['previous_monitor_time'] = 0
            #self.previous_measurement = 0
            #self.previous_monitor_time = 0

            network_metric['switch_dpid'] = int(str(next_node.dpid), 16)
            network_metric['metric_key'] = metric
            #self.switch_dpid = int(str(next_node.dpid), 16)
            #self.metric_key = '{0}_{1}'.format(direction, metric)

            self.network_metrics.append(network_metric)

            logging.info('Started monitoring: {2} on {0}:{1}'.format(vnf_name, vnf_interface, metric))
            return 'Started monitoring: {2} on {0}:{1}'.format(vnf_name, vnf_interface, metric)

        except Exception as ex:
            logging.exception("get_rate error.")
            return ex.message


    # get all metrics defined in the list
    def get_network_metrics(self):
        while True:
            # group metrics by dpid to optimize the rest api calls
            dpid_list = [metric_dict['switch_dpid'] for metric_dict in self.network_metrics]
            dpid_set = set(dpid_list)

            for dpid in dpid_set:

                # query Ryu
                ret = self.REST_cmd('stats/port', dpid)
                port_stat_dict = ast.literal_eval(ret)

                metric_list = [metric_dict for metric_dict in self.network_metrics
                               if int(metric_dict['switch_dpid'])==int(dpid)]
                #logging.info('1set prom packets:{0} '.format(self.network_metrics))
                for metric_dict in metric_list:
                    self.set_network_metric(metric_dict, port_stat_dict)

            time.sleep(1)

    # call this function repeatedly for streaming measurements
    def set_network_metric(self, metric_dict, port_stat_dict):

        metric_key = metric_dict['metric_key']
        switch_dpid = metric_dict['switch_dpid']
        vnf_name = metric_dict['vnf_name']
        vnf_interface = metric_dict['vnf_interface']
        previous_measurement = metric_dict['previous_measurement']
        previous_monitor_time = metric_dict['previous_monitor_time']
        mon_port = metric_dict['mon_port']

        for port_stat in port_stat_dict[str(switch_dpid)]:
            if int(port_stat['port_no']) == int(mon_port):
                port_uptime = port_stat['duration_sec'] + port_stat['duration_nsec'] * 10 ** (-9)
                this_measurement = int(port_stat[metric_key])
                #logging.info('set prom packets:{0} {1}:{2}'.format(this_measurement, vnf_name, vnf_interface))

                # set prometheus metric
                self.prom_metrics[metric_key].labels(vnf_name, vnf_interface).set(this_measurement)

                if previous_monitor_time <= 0 or previous_monitor_time >= port_uptime:
                    metric_dict['previous_measurement'] = int(port_stat[metric_key])
                    metric_dict['previous_monitor_time'] = port_uptime
                    # do first measurement
                    #logging.info('first measurement')
                    time.sleep(1)
                    byte_rate = self.get_network_metrics()
                    return byte_rate
                else:
                    time_delta = (port_uptime - metric_dict['previous_monitor_time'])
                    byte_rate = (this_measurement - metric_dict['previous_measurement']) / float(time_delta)
                    # logging.info('uptime:{2} delta:{0} rate:{1}'.format(time_delta,byte_rate,port_uptime))

                metric_dict['previous_measurement'] = this_measurement
                metric_dict['previous_monitor_time'] = port_uptime
                return byte_rate

        logging.exception('metric {0} not found on {1}:{2}'.format(metric_key, vnf_name, vnf_interface))
        return 'metric {0} not found on {1}:{2}'.format(metric_key, vnf_name, vnf_interface)


    # call this function repeatedly for streaming measurements
    def get_rate(self, vnf_name, vnf_interface=None, direction='tx', metric='packets'):

            key = self.metric_key

            ret = self.REST_cmd('stats/port', self.switch_dpid)
            port_stat_dict = ast.literal_eval(ret)
            for port_stat in port_stat_dict[str(self.switch_dpid)]:
                if port_stat['port_no'] == self.mon_port:
                    port_uptime = port_stat['duration_sec'] + port_stat['duration_nsec'] * 10 ** (-9)
                    this_measurement = int(port_stat[key])
                    #logging.info('packets:{0}'.format(this_measurement))

                    # set prometheus metrics
                    if metric == 'packets':
                        self.prom_tx_packet_count.labels(self.vnf_name, self.vnf_interface).set(this_measurement)
                    elif metric == 'bytes':
                        self.prom_tx_byte_count.labels(self.vnf_name, self.vnf_interface).set(this_measurement)

                    if self.previous_monitor_time <= 0 or self.previous_monitor_time >= port_uptime:
                        self.previous_measurement = int(port_stat[key])
                        self.previous_monitor_time = port_uptime
                        # do first measurement
                        time.sleep(1)
                        byte_rate = self.get_rate(vnf_name, vnf_interface, direction, metric)
                        return byte_rate
                    else:
                        time_delta = (port_uptime - self.previous_monitor_time)
                        byte_rate = (this_measurement - self.previous_measurement) / float(time_delta)
                        #logging.info('uptime:{2} delta:{0} rate:{1}'.format(time_delta,byte_rate,port_uptime))

                    self.previous_measurement = this_measurement
                    self.previous_monitor_time = port_uptime
                    return byte_rate

            return ret

    def REST_cmd(self, prefix, dpid):
        url = self.REST_api + '/' + str(prefix) + '/' + str(dpid)
        req = urllib2.Request(url)
        ret = urllib2.urlopen(req).read()
        return ret

    def start_Prometheus(self, port=9090):
        cmd = ["docker",
               "run",
               "--rm",
               "-p", "{0}:9090".format(port),
               "-v", "{0}/prometheus.yml:/etc/prometheus/prometheus.yml".format(getcwd()),
               "--name", "prometheus",
               "prom/prometheus"
               ]

        self.prometheus_process = Popen(cmd)

    def start_cAdvisor(self, port=8090):
        cmd = ["docker",
               "run",
               "--rm",
               "--volume=/:/rootfs:ro",
               "--volume=/var/run:/var/run:rw",
               "--volume=/sys:/sys:ro",
               "--volume=/var/lib/docker/:/var/lib/docker:ro",
               "--publish={0}:8080".format(port),
               "--name=cadvisor",
               "google/cadvisor:latest"
               ]
        self.cAdvisor_process = Popen(cmd)

    def stop(self):
        if self.prometheus_process is not None:
            self.prometheus_process.terminate()
            self.prometheus_process.kill()

        if self.cAdvisor_process is not None:
            self.cAdvisor_process.terminate()
            self.cAdvisor_process.kill()
