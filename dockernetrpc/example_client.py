import Pyro4


def main():
    # create connection to remote Mininet instance
    rmn = Pyro4.Proxy("PYRONAME:remote.mininet")

    # do some API tests
    h1 = rmn.addHost('h1')
    h2 = rmn.addHost('h2')
    #d1 = rmn.addDocker('d1', ip='10.0.0.253', dimage="ubuntu")

    s1 = rmn.addSwitch("s1")

    rmn.addLink(h1, s1)
    rmn.addLink(h2, s1)

    rmn.start()

    h3 = rmn.addHost('h3', ip='10.0.0.200')
    rmn.addLink(h3, s1)

    rmn.stop()


if __name__ == '__main__':
    main()
