import uuid


class PortPairGroup(object):
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.tenant_id = "abcdefghijklmnopqrstuvwxyz123456"
        self.name = name
        self.description = ""
        self.port_pairs = list()
        self.port_pair_group_parameters = dict()

    def create_dict(self, compute):
        representation = {
            "name": self.name,
            "tenant_id": self.tenant_id,
            "description": self.description,
            "port_pairs": self.port_pairs,
            "port_pair_group_parameters": self.port_pair_group_parameters,
            "id": self.id
        }
        return representation
