class LoadBalancer(object):
    def __init__(self, name, id=None, flavor=None, image=None, command=None, nw_list=None):
        self.name = name
        self.id = id  # not set
        self.out_ports = dict()
        self.in_ports = dict()
