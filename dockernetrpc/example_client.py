import Pyro4
import time


def main():
    # create connection to remote Mininet instance
    rmn = Pyro4.Proxy("PYRONAME:remote.mininet")

    # do some API tests
    h1 = rmn.addHost('h1')
    h2 = rmn.addHost('h2')
    d1 = rmn.addDocker('d1', ip='10.0.0.253', dimage="ubuntu")

    s1 = rmn.addSwitch("s1")

    rmn.addLink(h1, s1)
    rmn.addLink(h2, s1)
    rmn.addLink(d1, s1)

    rmn.start()

    # check functionality at runtime
    """
    d2 = rmn.addDocker('d2', dimage="ubuntu")
    h3 = rmn.addHost('h3', ip='10.0.0.200')
    rmn.addLink(d2, s1, params1={"ip": "10.0.0.251/8"})

    time.sleep(2)
    rmn.removeLink(node1="h1", node2="s1")
    rmn.removeHost('h1')
    #rmn.removeHost('d1')
    """

    time.sleep(2)
    rmn.stop()


if __name__ == '__main__':
    main()
