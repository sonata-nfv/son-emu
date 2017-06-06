import uuid


class InstanceFlavor:
    def __init__(self, name, cpu=None, memory=None, memory_unit=None, storage=None, storage_unit=None):
        self.id = str(uuid.uuid4())
        self.name = name
        self.cpu = cpu
        self.memory = memory
        self.memory_unit = memory_unit
        self.storage = storage
        self.storage_unit = storage_unit
