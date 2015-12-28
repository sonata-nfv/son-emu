import time
import zerorpc


def main():
    # create connection to remote Mininet instance
    c = zerorpc.Client()
    c.connect("tcp://127.0.0.1:4242")

    # do some API tests
    h1 = c.addHost('h1')
    h2 = c.addHost('h2')
    d1 = c.addDocker('d1', "ubuntu", "10.0.0.253")

    s1 = c.addSwitch("s1")

    c.addLink(h1, s1)
    c.addLink(h2, s1)
    c.addLink(d1, s1)

    c.start_net()
    c.CLI()

    # check functionality at runtime
    """
    d2 = c.addDocker('d2', dimage="ubuntu")
    h3 = c.addHost('h3', ip='10.0.0.200')
    c.addLink(d2, s1, params1={"ip": "10.0.0.251/8"})

    time.sleep(2)
    c.removeLink(node1="h1", node2="s1")
    c.removeHost('h1')
    #c.removeHost('d1')
    """

    time.sleep(2)
    c.stop_net()


if __name__ == '__main__':
    main()
