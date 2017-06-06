import uuid


class Stack:
    def __init__(self, id=None):
        self.servers = dict()
        self.nets = dict()
        self.ports = dict()
        self.routers = dict()
        self.stack_name = None
        self.creation_time = None
        self.update_time = None
        self.status = None
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id

    def add_server(self, server):
        """
        Adds one server to the server dictionary.

        :param server: The server to add.
        :type server: :class:`heat.resources.server`
        """
        self.servers[server.name] = server

    def add_net(self, net):
        """
        Adds one network to the network dictionary.

        :param net: Network to add.
        :type net: :class:`heat.resources.net`
        """
        self.nets[net.name] = net

    def add_port(self, port):
        """
        Adds one port to the port dictionary.

        :param port: Port to add.
        :type port: :class:`heat.resources.port`
        """
        self.ports[port.name] = port

    def add_router(self, router):
        """
        Adds one router to the port dictionary.

        :param router: Router to add.
        :type router: :class:`heat.resources.router`
        """
        self.routers[router.name] = router
