import threading

from flask import Flask
from flask_restplus import Resource, Api, fields, abort
import logging

from gevent.pywsgi import WSGIServer

from emuvim.dcemulator.net import DCNetwork

LOG = logging.getLogger("api.rest.SfcApiEndpoint")
LOG.setLevel(logging.INFO)

app = Flask(__name__)
api = Api(app)

pp = api.namespace('sfc/port_pairs', description='PortPair operations')
ppg = api.namespace('sfc/port_pair_groups', description='PortPairGroup operations')
pc = api.namespace('sfc/port_chains', description='PortChain operations')

portPair = api.model('Port Pair', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'vnf_src_name': fields.String(required=True, description='Name of the source VNF'),
    'vnf_dst_name': fields.String(required=True, description='Name of the destination VNF'),
    'vnf_src_interface': fields.String(required=True, description='Name of the source VNF interface'),
    'vnf_dst_interface': fields.String(required=True, description='Name of the dst VNF interface'),
})

portPairGroup = api.model('Port Pair Group', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'description': fields.String(description='useful information about the Port Pair Group'),
    'port_pairs': fields.List(fields.Integer, required=True, description='Port Pairs of equal VNFs')
})

portChain = api.model('Port Chain', {
    'id': fields.Integer(readonly=True, description='unique identifier'),
    'description': fields.String(description='useful information about the Port Chain'),
    'port_pair_groups': fields.List(fields.Integer, required=True,
                                    description='PortPairGroups, the order will be preserved'),
    'chain_id': fields.String(readonly=True, description='Reference to the Rendered Service Path')
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
        if id is None:
            return net.sfc_get_port_pair(None)

    def create(self, data):
        global net
        return net.sfc_add_port_pair(vnf_src_name=data['vnf_src_name'],
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
@pc.route('/')
class PortChains(Resource):
    """ Show Port Chains and add some"""

    @pc.doc('list_port_chains')
    @pc.marshal_list_with(portChain)
    def get(self):
        response = net.sfc_data.get_port_chains()
        if response is None:
            abort(404)
        else:
            return response

    @pc.response(409, 'Port chain not found, create port pair group before assign in port chain')
    @pc.doc('create_port_chain')
    @pc.expect(portChain)
    @pc.marshal_list_with(portChain, code=201)
    def post(self):
        """ Add port chain """
        new_port_exitchain = net.sfc_add_port_chain(description=api.payload['description'],
                                                port_pair_groups=api.payload['port_pair_groups'])
        if new_port_chain is None:
            abort(409)
        else:
            return new_port_chain


@pc.route('/<int:id>')
@pc.response(404, 'Port chain not found')
@pc.param('id', 'Port chain identifier')
class PortChain(Resource):
    """ Show a single port chain, or delete them """

    @pc.doc('get_port_chain')
    @pc.marshal_with(portChain)
    def get(self, id):
        """ Fetch a port pair group """
        response = net.sfc_data.get_port_chain(id)
        if response is None:
            abort(404)
        else:
            return response

    @pc.doc('delete_port_chain')
    @pc.response(204, 'Port chain deleted')
    def delete(self, id):
        """ Delete a port pair group """
        net.sfc_data.delete_port_chain(id)
        return '', 200  # 204 not possible, because flask returns content length 3 and thats not compliant


@ppg.route('/')
class PortPairGroups(Resource):
    """ Show Port Pair Groups and add some"""

    @ppg.doc('list_port_pair_groups')
    @ppg.marshal_list_with(portPairGroup)
    def get(self):
        response = net.sfc_data.get_port_pair_groups()
        if response is None:
            abort(404)
        else:
            return response

    @ppg.response(409, 'Port pair not found, create port pair before assign in port pair group')
    @ppg.doc('create_port_pair')
    @ppg.expect(portPairGroup)
    @ppg.marshal_list_with(portPairGroup, code=201)
    def post(self):
        """ Add port pair group """
        new_port_pair_group = net.sfc_add_port_pair_group(description=api.payload['description'],
                                                          port_pairs=api.payload['port_pairs'])
        if new_port_pair_group is None:
            abort(409)
        else:
            return new_port_pair_group


@ppg.route('/<int:id>')
@ppg.response(404, 'Port pair group not found')
@ppg.param('id', 'Port pair group identifier')
class PortPairGroup(Resource):
    """ Show a single port pair group, or delete them """

    @ppg.doc('get_port_pair_group')
    @ppg.marshal_with(portPairGroup)
    def get(self, id):
        """ Fetch a port pair group """
        response = net.sfc_data.get_port_pair_group(id)
        if response is None:
            abort(404)
        else:
            return response

    @ppg.doc('delete_port_pair_group')
    @ppg.response(204, 'Port pair group deleted')
    def delete(self, id):
        """ Delete a port pair group """
        net.sfc_data.delete_port_pair_group(id)
        return '', 200  # 204 not possible, because flask returns content length 3 and thats not compliant


@pp.route('/')
class PortPairs(Resource):
    """ Show all Port Pairs and add some """

    @pp.doc('list_port_pairs')
    @pp.marshal_list_with(portPair)
    def get(self):
        """ Fetch all port pairs"""
        return net.sfc_get_port_pair(None)

    @pp.doc('create_port_pair')
    @pp.expect(portPair)
    @pp.marshal_list_with(portPair, code=201)
    def post(self):
        """ Create a new port pair """
        return ppDAO.create(api.payload), 201


@pp.route('/<int:id>')
@pp.response(404, 'Port pair not found')
@pp.param('id', 'Port pair identifier')
class PortPair(Resource):
    """ Show a single port pair, or delete them """

    @pp.doc('get_port_pair')
    @pp.marshal_with(portPair)
    def get(self, id):
        """ Fetch a port pair """
        response = net.sfc_data.get_port_pair(id)
        if response is None:
            abort(404)
        else:
            return response

    @pp.doc('delete_todo')
    @pp.response(204, 'Todo deleted')
    def delete(self, id):
        """ Delete a port pair """
        net.sfc_delete_port_pair(id)
        return '', 200  # 204 not possible, because flask returns content length 3 and thats not compliant
