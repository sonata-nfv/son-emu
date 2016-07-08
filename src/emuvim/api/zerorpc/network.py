"""
Copyright (c) 2015 SONATA-NFV
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
"""
Distributed Cloud Emulator (dcemulator)
"""

import logging
import threading
import zerorpc


logging.basicConfig(level=logging.INFO)


class ZeroRpcApiEndpointDCNetwork(object):
    """
    Simple API endpoint that offers a zerorpc-based
    interface. This interface will be used by the
    default command line client.
    It can be used as a reference to implement
    REST interfaces providing the same semantics,
    like e.g. OpenStack compute API.
    """

    def __init__(self, listenip, port, DCNetwork=None):
        if DCNetwork :
            self.connectDCNetwork(DCNetwork)
        self.ip = listenip
        self.port = port
        logging.debug("Created monitoring API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def connectDCNetwork(self, net):
        self.net = net
        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def start(self):
        thread = threading.Thread(target=self._api_server_thread, args=())
        thread.daemon = True
        thread.start()
        logging.debug("Started API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def _api_server_thread(self):
        s = zerorpc.Server(DCNetworkApi(self.net))
        s.bind("tcp://%s:%d" % (self.ip, self.port))
        s.run()

    def stop(self):
        logging.info("Stop the monitoring API endpoint")
        return


class DCNetworkApi(object):
    """
        The networking and monitoring commands need the scope of the
        whole DC network to find the requested vnf. So this API is intended
        to work with a DCNetwork.
        Just pass through the corresponding request to the
        selected data center network. Do not implement provisioning
        logic here because will will have multiple API
        endpoint implementations at the end.
    """

    def __init__(self, net):
        self.net = net

    def network_action_start(self, vnf_src_name, vnf_dst_name, kwargs):
        # call DCNetwork method, not really datacenter specific API for now...
        # provided dc name needs to be part of API endpoint
        # no check if vnfs are really connected to this datacenter...
        logging.debug("RPC CALL: network chain start")
        try:
            c = self.net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=kwargs.get('vnf_src_interface'),
                vnf_dst_interface=kwargs.get('vnf_dst_interface'),
                cmd='add-flow',
                weight=kwargs.get('weight'),
                match=kwargs.get('match'),
                bidirectional=kwargs.get('bidirectional'),
                cookie=kwargs.get('cookie'))
            return str(c)
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def network_action_stop(self, vnf_src_name, vnf_dst_name, kwargs):
        # call DCNetwork method, not really datacenter specific API for now...
        # provided dc name needs to be part of API endpoint
        # no check if vnfs are really connected to this datacenter...
        logging.debug("RPC CALL: network chain stop")
        try:
            c = self.net.setChain(
                vnf_src_name, vnf_dst_name,
                vnf_src_interface=kwargs.get('vnf_src_interface'),
                vnf_dst_interface=kwargs.get('vnf_dst_interface'),
                cmd='del-flows',
                weight=kwargs.get('weight'),
                match=kwargs.get('match'),
                bidirectional=kwargs.get('bidirectional'),
                cookie=kwargs.get('cookie'))
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    # setup the rate measurement for a vnf interface
    def setup_metric(self, vnf_name, vnf_interface, metric):
        logging.debug("RPC CALL: setup metric")
        try:
            c = self.net.monitor_agent.setup_metric(vnf_name, vnf_interface, metric)
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    # remove the rate measurement for a vnf interface
    def stop_metric(self, vnf_name, vnf_interface, metric):
        logging.debug("RPC CALL: stop metric")
        try:
            c = self.net.monitor_agent.stop_metric(vnf_name, vnf_interface, metric)
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    # setup the flow metrics measurement
    def setup_flow(self, vnf_name, vnf_interface, metric, cookie):
        logging.debug("RPC CALL: setup flow")
        try:
            c = self.net.monitor_agent.setup_flow(vnf_name, vnf_interface, metric, cookie)
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    # remove the flow metrics measurement
    def stop_flow(self, vnf_name, vnf_interface, metric, cookie):
        logging.debug("RPC CALL: stop flow")
        try:
            c = self.net.monitor_agent.stop_flow(vnf_name, vnf_interface, metric, cookie)
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    # do prometheus query
    def prometheus(self, dc_label, vnf_name, vnf_interface, query):
        logging.debug("RPC CALL: query prometheus")
        vnf_status = self.net.dcs.get(dc_label).containers.get(vnf_name).getStatus()
        uuid = vnf_status['id']
        query = query.replace('<uuid>', uuid)
        #if needed, replace interface id with emu-intfs name
        # query = query.replace('<intf>', vnf_interface)
        logging.info('query: {0}'.format(query))
        try:
            c = self.net.monitor_agent.query_Prometheus(query)
            return c
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message



