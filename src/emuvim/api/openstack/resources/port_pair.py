import uuid


class PortPair(object):
    def __init__(self, name):
        self.id = str(uuid.uuid4())
        self.tenant_id = "abcdefghijklmnopqrstuvwxyz123456"
        self.name = name
        self.description = ""
        self.ingress = None
        self.egress = None
        self.service_function_parameters = dict()

    def create_dict(self, compute):
        representation = {
            "name": self.name,
            "tenant_id": self.tenant_id,
            "description": self.description,
            "ingress": self.ingress.id,
            "egress": self.egress.id,
            "id": self.id
        }
        return representation
