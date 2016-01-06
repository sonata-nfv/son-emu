"""
Distributed Cloud Emulator (dcemulator)
(c) 2015 by Manuel Peuster <manuel.peuster@upb.de>
"""

import logging
import threading
import zerorpc

logging.basicConfig(level=logging.DEBUG)


class ZeroRpcApiEndpoint(object):

    def __init__(self, listenip, port):
        self.dcs = {}
        self.ip = listenip
        self.port = port
        logging.debug("Created API endpoint %s(%s:%d)" % (
            self.__class__.__name__, self.ip, self.port))

    def connectDatacenter(self, dc):
        self.dcs[dc.name] = dc
        logging.info("Connected DC(%s) to API endpoint %s(%s:%d)" % (
            dc.name, self.__class__.__name__, self.ip, self.port))

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

    def __init__(self, dcs):
        self.dcs = dcs

    def compute_action_start(self, dc_name, compute_name):
        # TODO return UUID / IP ?
        logging.debug("RPC CALL: compute start")
        if dc_name in self.dcs:
            self.dcs[dc_name].addCompute(compute_name)

    def compute_action_stop(self, dc_name, compute_name):
        logging.info("compute stop")
        if dc_name in self.dcs:
            self.dcs[dc_name].removeCompute(compute_name)

    def compute_list(self):
        pass
