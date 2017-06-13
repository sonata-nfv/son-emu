from flask import Flask, request
from flask_restful import Api, Resource
import logging


class BaseOpenstackDummy(Resource):
    """
    This class is the base class for all openstack entrypoints of son-emu.
    """

    def __init__(self, listenip, port):
        self.ip = listenip
        self.port = port
        self.compute = None
        self.manage = None
        self.playbook_file = '/tmp/son-emu-requests.log'
        with open(self.playbook_file, 'w'):
            pass

        # setup Flask
        self.app = Flask(__name__)
        self.api = Api(self.app)

    def _start_flask(self):
        logging.info("Starting %s endpoint @ http://%s:%d" % (__name__, self.ip, self.port))
        if self.app is not None:
            self.app.before_request(self.dump_playbook)
            self.app.run(self.ip, self.port, debug=True, use_reloader=False)

    def dump_playbook(self):
        with self.manage.lock:
            with open(self.playbook_file, 'a') as logfile:
                if len(request.data) > 0:
                    data = "# %s API\n" % str(self.__class__).split('.')[-1].rstrip('\'>')
                    data += "curl -X {type} -H \"Content-type: application/json\" -d '{data}' {url}".format(type=request.method,
                                                                                            data=request.data,
                                                                                            url=request.url)
                    logfile.write(data + "\n")
