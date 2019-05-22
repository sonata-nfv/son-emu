from flask import Flask, request
from flask_restplus import Api, fields, Resource
from gevent.pywsgi import WSGIServer
from scapy.all import *
from scapy.contrib.nsh import *
import time

from werkzeug.contrib.fixers import ProxyFix

packet_counter = 0
SFC1 = 1
SFC3 = 1
iface = None
running = True

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='SFC results API',
          description='API for submitting SFC results', )

change_behavior = api.model('ChangeBehavior', {
    'sfc1': fields.Integer(),
    'sfc3': fields.Integer()
})


class ClassifierApiEndpoint(object):
    def __init__(self, ip="0.0.0.0", port=6161):
        self.thread = threading.Thread(target=self._start_flask, args=())
        self.ip = ip
        self.port = port

    def start(self):
        self.thread.daemon = True
        self.thread.start()

    def stop(self):
        if self.http_server:
            self.http_server.close()

    def _start_flask(self):
        self.http_server = WSGIServer((self.ip, self.port),
                                      app,
                                      # This disables HTTP request logs to not
                                      # mess up the CLI when e.g. the
                                      # auto-updated dashboard is used
                                      log=open("/dev/null", "w")
                                      )
        self.http_server.serve_forever()


@api.route('/')
class ChangeBehavior(Resource):
    """Receive feedback from SFC entities"""

    @api.doc('create_diagram')
    @api.expect(change_behavior)
    @api.marshal_with(change_behavior, code=200)
    def post(self):
        # process api.payload
        global SFC1, SFC3
        if "sfc1" in api.payload:
            SFC1 = api.payload['sfc1']
        if "sfc3" in api.payload:
            SFC3 = api.payload['sfc3']
        return api.payload

    @api.doc('shut down classifier')
    def delete(self):
        global running
        running = False


def _send(nsh):
    sendp(Ether() / nsh /
          Ether() / IP(), iface=iface)


class Flow(Thread):
    def __init__(self, rate, spi, si, n_packets):
        super(Flow, self).__init__()
        self.timeout = float(1) / rate
        self.spi = spi
        self.si = si
        self.stop = False
        self.n_packets = n_packets

    def run(self):
        for i in range(0, self.n_packets):
            _send(NSH(SPI=self.spi, SI=self.si))
            time.sleep(self.timeout)


def main():
    """
    Classifier provides the traffic story. It both creates the traffic, that would normally be sent to the classifier,
    executes classification on it and sends the data with the proper NSH encapsulation to the connected SFF at "out".
    The classifier also enables a behaviour for interactive policy updating.
    :return:
    """
    time.sleep(0)
    flow1 = Flow(30, 2, 4, 400)
    flow1.start()
    time.sleep(65)

    flow1.join(2)
    flow2.join(2)
    flow3.join(2)
    # more_complex()


def _print_help():
    print("Bad argument. Provide SFC interface name \nExample: %s eth0" % sys.argv[0])


if __name__ == '__main__':
    iface = "out"
    ep = ClassifierApiEndpoint()
    ep.start()
    main()

    ep.stop()
