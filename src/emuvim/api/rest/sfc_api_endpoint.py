import threading

from flask import Flask
from flask_restplus import Resource, Api, fields
import logging

from gevent.pywsgi import WSGIServer

from emuvim.dcemulator.net import DCNetwork

LOG = logging.getLogger("api.rest.SfcApiEndpoint")
LOG.setLevel(logging.INFO)

app = Flask(__name__)
api = Api(app)

pp = api.namespace('portPair', description='PortPair operations')
ppg = api.namespace('portPairGroup', description='PortPairGroup operations')
pc = api.namespace('portChain', description='PortChain operations')

portPair = api.model('Port Pair', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'vnf_src_name': fields.String(required=True, description='Name of the source VNF'),
    'vnf_dst_name': fields.String(required=True, description='Name of the destination VNF'),
    'vnf_src_interface': fields.String(required=True, description='Name of the source VNF interface'),
    'vnf_dst_interface': fields.String(required=True, description='Name of the dst VNF interface'),
})

portPairGroup = api.model('Port Pair Group', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'port_pairs': fields.List(fields.Integer, required=True, description='Port Pairs of equal VNFs')
})

portChain = api.model('Port Chain', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'port_pair_groups': fields.List(fields.Integer, required=True,
                                    description='PortPairGroups, the order will be preserved'),
    'status': fields.String(readonly=True, description='status of SFC: (FAILURE: <message>), (DEPLOYED)')

})
net = None  # type: DCNetwork


class SfcApiEndpoint(object):
    def __init__(self, listenip, port, ):
        LOG.info("blubberquark")

    def start(self):
        self.thread = threading.Thread(target=self._start_flask, args=())
        self.thread.daemon = True
        self.thread.start()

    def connect_dc_network(self, dc_network):
        global net
        logging.info("Connected DCNetwork to API endpoint %s(%s:%d)")
        net = dc_network

    def stop(self):
        if self.http_server:
            self.http_server.close()

    def _start_flask(self):
        # self.app.run(self.ip, self.port, debug=False, use_reloader=False)
        # this should be a more production-fit http-server
        # self.app.logger.setLevel(logging.ERROR)
        self.http_server = WSGIServer(("0.0.0.0", 5000),
                                      app,
                                      # This disables HTTP request logs to not
                                      # mess up the CLI when e.g. the
                                      # auto-updated dashboard is used
                                      log=open("/dev/null", "w")
                                      )
        self.http_server.serve_forever()


class PortPairDAO(object):
    def __init__(self):
        self.counter = 0
        self.portPairs = []

    def get(self, id):
        for portPair in self.portPairs:
            if portPair['id'] == id:
                return portPair
        api.abort(404, "PortPair {} does not exist".format(id))

    def create(self, data):
        global net
        return net.make_something_with_sfc(vnf_src_name=data['vnf_src_name'],
                                           vnf_src_interface=data['vnf_src_interface'],
                                           vnf_dst_name=data['vnf_dst_name'],
                                           vnf_dst_interface=data['vnf_dst_interface'])

    def update(self, id, data):
        api.abort(404, "not implemented")

    def delete(self, id):
        api.abort(404, "not implemented")


ppDAO = PortPairDAO()


# ppDAO.create({'vnf_src_name': 'vnfsrc',               'vnf_dst_name': 'vnfdst',               'vnf_src_interface':
# 'vnfsrciface',               'vnf_dst_interface': 'vnfdstiface'               })


@pp.route('/')
class PortPairList(Resource):
    """ Show all Port Pairs and add some """

    @pp.doc('list_port_pairs')
    @pp.marshal_list_with(portPair)
    def get(self):
        return ppDAO.portPairs

    @pp.doc('create_port_pair')
    @pp.expect(portPair)
    @pp.marshal_list_with(portPair, code=201)
    def post(self):
        """ Create a new PortPair """
        # print(api.payload)
        return ppDAO.create(api.payload), 201
