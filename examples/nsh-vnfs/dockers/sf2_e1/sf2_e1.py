from sf import *


class ExperimentSniffer(Sniffer):
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

                    # if len(sfc_result.packet_received_at) > 200 and spi is 2:
                    if metadata > 600 and spi is 2:
                        metadata = metadata ^ (2 ** 32) # set flag for SF3
                    send_nsh(NSH(SPI=spi, SI=si - 1, FContextHeader=metadata), iface)
                    print("SPI=%d SI=%d Metadata=%d received, and some more" % (spi, si, metadata))
                except AttributeError:
                    print("received unconfigured SPI/SI pair: (%d,%d)" % (spi, si))

if __name__ == '__main__':
    sf_name = "SF2"
    iface = "sfc"
    # classifier_ip = "10.0.0.10"
    # classifier_port = 6161
    report_ip = "172.17.0.2"
    report_port = 6162
    duration = 70  # execution time in seconds of the experiment

    store = SFCResultStore(sf_name, report_ip, report_port)
    store.add_result(SFCResult(1, 2))
    store.add_result(SFCResult(2, 3))
    store.add_result(SFCResult(4, 2))

    sniffer = ExperimentSniffer(interface=iface)
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
