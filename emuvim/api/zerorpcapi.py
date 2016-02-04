"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""

import logging
import threading
import zerorpc

logging.basicConfig(level=logging.INFO)


class ZeroRpcApiEndpoint(object):
    """
    Simple API endpoint that offers a zerorpc-based
    interface. This interface will be used by the
    default command line client.
    It can be used as a reference to implement
    REST interfaces providing the same semantics,
    like e.g. OpenStack compute API.
    """

    def __init__(self, listenip, port):
        self.dcs = {}
        self.ip = listenip
        self.port = port
        logging.debug("Created API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def connectDatacenter(self, dc):
        self.dcs[dc.label] = dc
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" % (
            dc.label, self.__class__.__name__, self.ip, self.port))

    def start(self):
        thread = threading.Thread(target=self._api_server_thread, args=())
        thread.daemon = True
        thread.start()
        logging.debug("Started API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def _api_server_thread(self):
        s = zerorpc.Server(MultiDatacenterApi(self.dcs))
        s.bind("tcp://%s:%d" % (self.ip, self.port))
        s.run()


class MultiDatacenterApi(object):
    """
        Just pass through the corresponding request to the
        selected data center. Do not implement provisioning
        logic here because will will have multiple API
        endpoint implementations at the end.
    """

    def __init__(self, dcs):
        self.dcs = dcs

    def compute_action_start(self, dc_name, compute_name, image, network):
        # network e.g. {"ip": "10.0.0.254/8"}
        # TODO what to return UUID / given name / internal name ?
        logging.debug("RPC CALL: compute start")
        try:
            c = self.dcs.get(dc_name).startCompute(
                compute_name, image=image, network=network)
            return str(c.name)
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def compute_action_stop(self, dc_name, compute_name):
        logging.debug("RPC CALL: compute stop")
        try:
            return self.dcs.get(dc_name).stopCompute(compute_name)
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def compute_list(self, dc_name):
        logging.debug("RPC CALL: compute list")
        try:
            if dc_name is None:
                # return list with all compute nodes in all DCs
                all_containers = []
                for dc in self.dcs.itervalues():
                    all_containers += dc.listCompute()
                return [(c.name, c.getStatus())
                        for c in all_containers]
            else:
                # return list of compute nodes for specified DC
                return [(c.name, c.getStatus())
                        for c in self.dcs.get(dc_name).listCompute()]
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def compute_status(self, dc_name, compute_name):
        logging.debug("RPC CALL: compute status")
        try:
            return self.dcs.get(
                dc_name).containers.get(compute_name).getStatus()
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message
