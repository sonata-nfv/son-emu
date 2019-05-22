#! /usr/bin/env python
import classifier
from classifier import *





if __name__ == '__main__':
    classifier.iface = "out"
    time.sleep(5)  # Wait for SFs to come up
    flow1 = Flow(10, 1, 2, 200) # sending rate, SPI, SI, number of packets
    flow2 = Flow(10, 2, 2, 200)
    flow1.start()
    time.sleep(20)
    flow2.start()
    time.sleep(70)
    flow1.stop=True
    flow2.stop=True
    flow1.join(2)
    flow2.join(2)

    # ep = ClassifierApiEndpoint()
    # ep.start()
    # ep.stop()
