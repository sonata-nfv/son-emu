import requests

from datastore import SFCResultStore, SFCResult
from scapy.layers.inet import IP
from scapy.layers.l2 import Ether
from scapy.all import *
from threading import Thread, Event
from time import sleep
from scapy.contrib.nsh import NSH

iface = ''
store = None  # SFCResultStore
sfc = ''
classifier_ip = None
classifier_port = None


class Submitter(Thread):
    def __init__(self):
        super(Submitter, self).__init__()
        self.stop = False

    def run(self):
        while not self.stop:
            # Stub
            self.stop = True


class Sniffer(Thread):

    def __init__(self, interface=iface):
        super(Sniffer, self).__init__()

        self.daemon = True
        self.socket = None
        self.interface = interface
        self.stop_sniffer = Event()
        self.n_packets = 0

    def run(self):
        self.socket = conf.L2listen(
            type=ETH_P_ALL,
            iface=self.interface
        )

        sniff(
            opened_socket=self.socket,
            prn=self.process_packet,
            store=0
        )

    def join(self, timeout=None):
        self.stop_sniffer.set()
        super(Sniffer, self).join(timeout)

    def should_stop_sniffer(self, packet):
        return self.stop_sniffer.isSet()

    def process_packet(self, pkt):
        if NSH in pkt:  # who-has or is-at
            # pkt.show()
            nsh = pkt[NSH]
            if isinstance(nsh, NSH):
                spi = int(nsh.fields['SPI'])
                si = int(nsh.fields['SI'])
                metadata = int(nsh.fields['FContextHeader'])
                try:
                    sfc_result = store.get_result(spi, si)
                    sfc_result.receive(self.n_packets + 1, metadata)
                    self.n_packets += 1
                    # Story: For SFC 1 & 3: Deploy rule on classifier after receiving more than 100 packets.
                    # if spi is 1 and len(sfc_result.packet_received_at) > 50:
                    if spi is 1 and metadata > 300:
                        send_classifier_feedback({"sfc1": 2})

                    # if spi is 3 and len(sfc_result.packet_received_at) > 350:
                    if spi is 3 and metadata > 900:
                        send_classifier_feedback({"sfc3": 2})
                    send_nsh(NSH(SPI=spi, SI=si - 1, FContextHeader=metadata), self.interface)
                    print("SPI=%d SI=%d Metadata=%d received" % (spi, si, metadata))
                except AttributeError:
                    print("received unconfigured SPI/SI pair: (%d,%d)" % (spi, si))


def send_nsh(nsh, a_iface=iface):
    sendp(Ether() / nsh /
          Ether() / IP(), iface=a_iface)


def send_classifier_feedback(feedback):
    """This function depends on the experiment. The submitted feedback argument must accord with the API Endpoint at
    the classifier, e.g. feedback = {"sfc": 2}"""
    global classifier_ip, classifier_port
    if classifier_ip is None or classifier_port is None:
        raise AttributeError("Cannot submit results due to missing classifier_ip or port")
    resp = requests.post("http://%s:%d/" % (classifier_ip, classifier_port), json=feedback)
    print(resp)


if __name__ == '__main__':
    """Parameters for the default SF. Classifier invocations are not implemented by default and can be implemented in
    experiments"""
    sf_name = "SF1"
    iface = "sfc"
    classifier_ip = "10.0.0.10"
    classifier_port = 6161
    report_ip = "172.17.0.2"
    report_port = 6162
    duration = 70  # execution time in seconds of the experiment

    store = SFCResultStore(sf_name, report_ip, report_port)
    store.add_result(SFCResult(1, 3))
    store.add_result(SFCResult(2, 4))
    store.add_result(SFCResult(3, 2))

    sniffer = Sniffer(interface=iface)
    submitter = Submitter()
    submitter.start()
    print("[*] Start sniffing...")
    sniffer.start()
    sleep(duration)
    print("[*] Stop sniffing")
    submitter.stop = True
    submitter.join(2.0)
    sniffer.join(2.0)
    if sniffer.isAlive():
        sniffer.socket.close()
    store.submit()  # Final submit of the results
