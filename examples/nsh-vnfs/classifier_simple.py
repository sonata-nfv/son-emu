#! /usr/bin/env python
import classifier
from classifier import *

def main():
    """
    Classifier provides the traffic story. It both creates the traffic, that would normally be sent to the classifier,
    executes classification on it and sends the data with the proper NSH encapsulation to the connected SFF at "out".
    The classifier also enables a behaviour for interactive policy updating.
    :return:
    """
    flow1 = Flow(10, 1, 2, 200)
    flow2 = Flow(10, 2, 2, 200)
    flow1.start()
    time.sleep(3)
    flow2.start()
    time.sleep(3)
    flow1.stop=True
    flow2.stop=True
    flow1.join(2)
    flow2.join(2)


if __name__ == '__main__':
    classifier.iface = ""
    time.sleep(5)  # Wait for SFs to come up
    main()

    # ep = ClassifierApiEndpoint()
    # ep.start()
    # ep.stop()
