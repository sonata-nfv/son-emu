import datetime
import json
import os

import numpy as np
import matplotlib

matplotlib.use('Agg')
import matplotlib.pyplot as plt
from flask import Flask
from flask_restplus import Resource, Api, fields
from werkzeug.contrib.fixers import ProxyFix

from datastore import SFCResultStore, SFCResult

app = Flask(__name__)
app.wsgi_app = ProxyFix(app.wsgi_app)
api = Api(app, version='1.0', title='SFC results API',
          description='API for submitting SFC results',
          )

sfc_result = api.model('SFCResult', {
    'spi': fields.Integer(required=True),
    'si': fields.Integer(required=True),
    'packet_received_at': fields.List(fields.Integer),
    'classifier_received_at': fields.List(fields.Integer)
})
result_container = api.model('SFCResultStore', {
    'sf_name': fields.String(required=True),
    'sfc_results': fields.List(fields.Nested(sfc_result))
})


def write_bar_diagram(sfc_result_stores):
    matplotlib.rcParams.update({'font.size': 14})
    n_groups = len(sfc_result_stores)
    n_packets_sf = {}
    spi_si_labels = []
    sf_names = []
    for sf_name, sfc_result_store in sfc_result_stores.items():
        n_packets = {}
        sf_names.append(sf_name)
        if isinstance(sfc_result_store, SFCResultStore):
            for sfc_res in sfc_result_store.sfc_results:
                if isinstance(sfc_res, SFCResult):
                    bar_label = format("%d" % sfc_res.spi)
                    if not any(bar_label in s for s in spi_si_labels):
                        spi_si_labels.append(bar_label)
                    n_packets[bar_label] = len(
                        sfc_res.packet_received_at)  # .append(len(sfc_result.packet_received_at))
        n_packets_sf[sf_name] = n_packets

    # figure out the input rows for matplotlib
    n_packets_by_spi_si = {}
    for bar_label in spi_si_labels:
        numbers = []
        for sf_name, sfc_result_store in sfc_result_stores.items():
            number = 0
            if bar_label in n_packets_sf[sf_name]:
                number = n_packets_sf[sf_name][bar_label]
            numbers.append(number)
        n_packets_by_spi_si[bar_label] = numbers

    fig, ax = plt.subplots()

    index = np.arange(n_groups)
    bar_width = float(len(sf_names)) / (n_groups * 10)
    opacity = 0.4
    count = 0
    for label, numbers in n_packets_by_spi_si.items():
        space = count * bar_width
        ax.bar(index + space, numbers, bar_width, alpha=opacity, label=label)
        # ax.bar(numbers, alpha=opacity, label=label)

        count += 1

    ax.set_xlabel('Name of Service Function')
    ax.set_ylabel('Number of received packets')
    ax.set_title('Number of received packets of SFs NSH SPI ')
    index_b = index + (bar_width * n_groups / 2)
    if len(spi_si_labels) % 2 == 0:
        index_b += bar_width / 2

    ax.set_xticks(index_b)
    ax.set_xticklabels(sf_names)
    ax.legend()
    print(n_packets)

    fig.tight_layout()
    my_path = os.path.dirname(os.path.realpath(__file__))
    my_file = 'fig/complete_' + datetime.datetime.now().isoformat().replace(":", "_") + '_bar.pdf'
    plt.savefig(os.path.join(my_path, my_file))
    # plt.show()
    plt.close()


class DataAccess:
    def __init__(self):
        self.sfc_result_stores = {}

    def process(self, data):
        sfcrstore = SFCResultStore(data['sf_name'])
        for sfcr in data['sfc_results']:
            print(sfcr['spi'])
            sfcr_obj = SFCResult(int(sfcr['spi']), int(sfcr['si']))
            sfcr_obj.packet_received_at = sfcr['packet_received_at']
            sfcr_obj.classifier_received_at = sfcr['classifier_received_at']
            sfcrstore.add_result(sfcr_obj)
        self.sfc_result_stores[data['sf_name']] = sfcrstore
        # start_time =  data['start_time'] # first received seq. no. of NSH packets
        print("data")
        # sfcrstore.write_bar_diagram()
        sfcrstore.write_time_diagram()
        write_bar_diagram(self.sfc_result_stores)
        # self.todos.append(todo)
        # return todo
        my_path = os.path.dirname(os.path.realpath(__file__))
        date = datetime.datetime.now().isoformat().replace(":", "_")
        my_file = 'fig/' + data['sf_name'] + date + '_raw.txt'

        with open(os.path.join(my_path, my_file), "w") as fp:
            json.dump(data, fp)
            fp.close()

    def reset(self):
        self.sfc_result_stores.clear()

    def mock_data(self, n_sfc, n_res, name):
        result_store = SFCResultStore(format("sf%d" % name), "127.0.0.1")

        for i in range(1, n_sfc):
            sfc_res = SFCResult(i, 42)
            for j in range(0, name + i - 1):
                sfc_res.receive(j)
            result_store.add_result(sfc_res)

        self.sfc_result_stores[result_store.sf_name] = result_store

    def test(self):
        for i in range(1, 3):
            self.mock_data(3, 8, i)

        print(self.sfc_result_stores)
        write_bar_diagram(self.sfc_result_stores)

        # result_store.write_time_diagram()
        # result_store.submit()


DAO = DataAccess()


@api.route('/')
class Result(Resource):
    """Submit results"""

    # @api.doc('list_todos')
    # @api.marshal_list_with(result_container)
    # def get(self):
    #     '''List all tasks'''
    #     return DAO.todos

    @api.doc('reset_results')
    def delete(self):
        DAO.reset()

    @api.doc('get_result')
    @api.expect(result_container)
    @api.marshal_with(result_container, code=201)
    def post(self):
        '''Create a new task'''
        return DAO.process(api.payload), 201


if __name__ == '__main__':
    app.run(debug=True, port=6162, host="0.0.0.0")
    # DAO.test()
