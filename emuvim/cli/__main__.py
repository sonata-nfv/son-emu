"""
 For now only a dummy client. Connects to the zerorpc interface of the
 emulator and performs some actions (start/stop/list).
"""
import time
import zerorpc


def main():
    print "Example CLI client"
    # create connection to remote Mininet instance
    c = zerorpc.Client()
    c.connect("tcp://127.0.0.1:4242")

    # do some API tests
    print c.compute_action_start("dc2", "my_new_container1")

    time.sleep(10)

    print c.compute_action_stop("dc2", "my_new_container1")


if __name__ == '__main__':
    main()
