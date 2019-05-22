import csv
import os
import json

import numpy as np
import matplotlib
from matplotlib.ticker import MaxNLocator

matplotlib.use('Agg')
import matplotlib.pyplot as plt
import requests


class SFCResultStore:
    def __init__(self, sfc_name, aggregator_ip=None, aggregator_port=None):
        self.sf_name = sfc_name
        self.sfc_results = []
        self.aggregator_ip = aggregator_ip
        self.aggregator_port = aggregator_port

    def add_result(self, sfc_result):
        self.sfc_results.append(sfc_result)

    def get_result(self, spi, si):
        for sfc_result in self.sfc_results:
            if isinstance(sfc_result, SFCResult) and sfc_result.si == si and sfc_result.spi == spi:
                return sfc_result
        return None

    def save(self):
        results = []
        for sfc_result in self.sfc_results:
            results.append(str(sfc_result.spi) + "/" + str(sfc_result.si))
        with open('eggs.csv', 'wb') as csvfile:
            spamwriter = csv.writer(csvfile, delimiter=',',
                                    quotechar='|', quoting=csv.QUOTE_MINIMAL)
            spamwriter.writerow(results)

    def write_bar_diagram(self):
        n_groups = len(self.sfc_results)
        n_packets = []
        x_labels = []
        for sfc_result in self.sfc_results:
            n_packets.append(len(sfc_result.packet_received_at))
            x_labels.append(format("(%d,%d)" % (sfc_result.spi, sfc_result.si)))

        means_men = (20, 35, 30, 35, 27)

        means_women = (25, 32, 34, 20, 25)

        fig, ax = plt.subplots()

        index = np.arange(n_groups)
        bar_width = 0.35

        opacity = 0.4
        error_config = {'ecolor': '0.3'}

        rects1 = ax.bar(index, n_packets, bar_width,
                        alpha=opacity, color='b')

        # rects2 = ax.bar(index + bar_width, means_women, bar_width,
        #                 alpha=opacity, color='r',
        #                 yerr=std_women, error_kw=error_config,
        #                 label='Women')

        ax.set_xlabel('(SPI,SI) of received packet')
        ax.set_ylabel('Scores')
        ax.set_title('Number of received packets by SPI/SI')
        ax.set_xticks(index + bar_width / 2)
        ax.set_xticklabels(x_labels)
        ax.legend()
        print(n_packets)

        fig.tight_layout()
        my_path = os.path.dirname(os.path.realpath(__file__))
        my_file = 'fig/' + self.sf_name + '_bar.pdf'
        plt.savefig(os.path.join(my_path, my_file))
        # plt.show()
        plt.close()

    def write_time_diagram(self):
        matplotlib.rcParams.update({'font.size': 14})
        fig, ax = plt.subplots()
        ax.set_title('Number of received packets by SPI/SI')
        for sfc_result in self.sfc_results:
            xa = []
            ya = []
            for i in range(0, len(sfc_result.packet_received_at)):
                ya.append(i + 1)
                xa.append(sfc_result.packet_received_at[i])

            x = xa  # np.linspace(0, 10, 500)
            y = ya  # np.sin(x)

            # Using set_dashes() to modify dashing of an existing line
            ax.plot(x, y, label=format("(%d,%d)" % (sfc_result.spi, sfc_result.si)))
        ax.yaxis.set_major_locator(MaxNLocator(integer=True))
        ax.xaxis.set_major_locator(MaxNLocator(integer=True))
        ax.set_ylabel("Received packets by (SPI,SI)-pair")
        ax.set_xlabel("Total received NSH-encapsulated packets")
        ax.legend()
        my_path = os.path.dirname(os.path.realpath(__file__))
        my_file = 'fig/' + self.sf_name + '_time.pdf'
        plt.savefig(os.path.join(my_path, my_file))
        plt.close()

    def submit(self):
        if self.aggregator_ip is None:
            raise AttributeError("Cannot submit results due to missing aggregator_ip for SFCResultStore")
        results = []
        for sfc_result in self.sfc_results:
            results.append(sfc_result.__dict__)
        task = {
            "sf_name": str(self.sf_name),
            "sfc_results":
                results

        }
        resp = requests.post("http://%s:%d/" % (self.aggregator_ip, self.aggregator_port), json=task)


class SFCResult:
    def __init__(self, spi, si):
        self.spi = int(spi)
        self.si = int(si)
        self.packet_received_at = []
        self.classifier_received_at = []

    def receive(self, stamp, classifier_stamp=0):
        self.packet_received_at.append(int(stamp))
        self.classifier_received_at.append(int(classifier_stamp))


if __name__ == '__main__':

    result_store = SFCResultStore("blubb", "127.0.0.1")
    sfc_res = SFCResult(123, '12')
    sfc_res.receive(1)
    sfc_res.receive('8')
    result_store.add_result(sfc_res)
    sfc_res.receive(17)
    sfc_res.receive(19)
    sfc_res.receive(20)

    sfc_res2 = SFCResult(1, '2')
    sfc_res2.receive(3)
    sfc_res2.receive('7')
    sfc_res2.receive(18)
    sfc_res2.receive(50)
    result_store.add_result(sfc_res2)
    result_store.write_bar_diagram()
    result_store.write_time_diagram()
    # result_store.submit()
    for result in result_store.sfc_results:
        if isinstance(result, SFCResult):
            print(result.packet_received_at)
