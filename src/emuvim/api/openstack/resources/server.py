class Server(object):
    def __init__(self, name, id=None, flavor=None, image=None, command=None, nw_list=None):
        self.name = name
        self.full_name = None
        self.template_name = None
        self.id = id
        self.image = image
        self.command = command
        self.port_names = list()
        self.flavor = flavor
        self.son_emu_command = None
        self.emulator_compute = None

    def compare_attributes(self, other):
        """
        Compares only class attributes like name and flavor but not the list of ports with the other server.

        :param other: The second server to compare with.
        :type other: :class:`heat.resources.server`
        :return: * *True*: If all attributes are alike.
            * *False*: Else
        :rtype: ``bool``
        """
        if self.name == other.name and self.full_name == other.full_name and \
                        self.flavor == other.flavor and \
                        self.image == other.image and \
                        self.command == other.command:
            return True
        return False

    def __eq__(self, other):
        if self.name == other.name and self.full_name == other.full_name and \
                        self.flavor == other.flavor and \
                        self.image == other.image and \
                        self.command == other.command and \
                        len(self.port_names) == len(other.port_names) and \
                        set(self.port_names) == set(other.port_names):
            return True
        return False

    def create_server_dict(self, compute=None):
        """
        Creates the server description dictionary.

        :param compute: The compute resource for further status information.
        :type compute: :class:`heat.compute`
        :return: Server description dictionary.
        :rtype: ``dict``
        """
        server_dict = dict()
        server_dict['name'] = self.name
        server_dict['full_name'] = self.full_name
        server_dict['id'] = self.id
        server_dict['template_name'] = self.template_name
        server_dict['flavor'] = self.flavor
        server_dict['image'] = self.image
        if self.son_emu_command is not None:
            server_dict['command'] = self.son_emu_command
        else:
            server_dict['command'] = self.command

        if compute is not None:
            server_dict['status'] = 'ACTIVE'
            server_dict['OS-EXT-STS:power_state'] = 1
            server_dict["OS-EXT-STS:task_state"] = None
        return server_dict
