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

    def compute_action_start(self, dc_label, compute_name, image, network=None, command=None):
        """
        Start a new compute instance: A docker container
        :param dc_label: name of the DC
        :param compute_name: compute container name
        :param image: image name
        :param command: command to execute
        :param network: list of all interface of the vnf, with their parameters (id=id1,ip=x.x.x.x/x),...
        :return: networks list({"id":"input","ip": "10.0.0.254/8"}, {"id":"output","ip": "11.0.0.254/24"})
        """
        # TODO what to return UUID / given name / internal name ?
        logging.debug("RPC CALL: compute start")
        try:
            c = self.dcs.get(dc_label).startCompute(
                compute_name, image=image, command=command, network=network)
            return str(c.name)
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def compute_action_stop(self, dc_label, compute_name):
        logging.debug("RPC CALL: compute stop")
        try:
            return self.dcs.get(dc_label).stopCompute(compute_name)
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def compute_list(self, dc_label):
        logging.debug("RPC CALL: compute list")
        try:
            if dc_label is None:
                # return list with all compute nodes in all DCs
                all_containers = []
                for dc in self.dcs.itervalues():
                    all_containers += dc.listCompute()
                return [(c.name, c.getStatus())
                        for c in all_containers]
            else:
                # return list of compute nodes for specified DC
                return [(c.name, c.getStatus())
                        for c in self.dcs.get(dc_label).listCompute()]
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def compute_status(self, dc_label, compute_name):
        logging.debug("RPC CALL: compute status")
        try:
            return self.dcs.get(
                dc_label).containers.get(compute_name).getStatus()
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def datacenter_list(self):
        logging.debug("RPC CALL: datacenter list")
        try:
            return [d.getStatus() for d in self.dcs.itervalues()]
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message

    def datacenter_status(self, dc_label):
        logging.debug("RPC CALL: datacenter status")
        try:
                return self.dcs.get(dc_label).getStatus()
        except Exception as ex:
            logging.exception("RPC error.")
            return ex.message
