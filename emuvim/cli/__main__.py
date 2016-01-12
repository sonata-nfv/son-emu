"""
 For now only a dummy client. Connects to the zerorpc interface of the
 emulator and performs some actions (start/stop/list).

 We will provide a full CLI here later on which looks like:

 cli compute start dc1 my_name flavor_a
 cli network create dc1 11.0.0.0/24
"""
import time
import zerorpc


def main():
    print "Example CLI client"
    # create connection to remote Mininet instance
    c = zerorpc.Client()
    c.connect("tcp://127.0.0.1:4242")

    # do some API tests
    print c.compute_action_start("dc2", "d1")
    print c.compute_action_start("dc2", "d2")

    time.sleep(20)

    print c.compute_action_stop("dc2", "d1")
    print c.compute_action_stop("dc2", "d2")


if __name__ == '__main__':
    main()
