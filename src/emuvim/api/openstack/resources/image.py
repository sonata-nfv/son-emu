import uuid
from datetime import datetime


class Image:
    def __init__(self, name, id=None):
        self.name = name
        if id is None:
            self.id = str(uuid.uuid4())
        else:
            self.id = id
        self.created = str(datetime.now())

    def __eq__(self, other):
        if self.name == other.name:
            return True
        return False
