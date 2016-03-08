"""
This module implements a simple REST API that behaves like SONATA's gatekeeper.

It is only used to support the development of SONATA's SDK tools and to demonstrate
the year 1 version of the emulator until the integration with WP4's orchestrator is done.
"""

import logging
import threading
import dummygatekeeper as dgk


class SonataDummyGatekeeperEndpoint(object):
    """
    Creates and starts a REST API based on Flask in an
    additional thread.

    Can connect this API to data centers defined in an emulator
    topology.
    """

    def __init__(self, listenip, port):
        self.dcs = {}
        self.ip = listenip
        self.port = port
        logging.debug("Created API endpoint %s" % self)

    def __repr__(self):
        return "%s(%s:%d)" % (self.__class__.__name__, self.ip, self.port)

    def connectDatacenter(self, dc):
        self.dcs[dc.label] = dc
        logging.info("Connected DC(%s) to API endpoint %s" % (
            dc, self))

    def start(self):
        thread = threading.Thread(target=self._api_server_thread, args=())
        thread.daemon = True
        thread.start()
        logging.debug("Started API endpoint %s" % self)

    def _api_server_thread(self):
        dgk.start_rest_api(self.ip, self.port)
