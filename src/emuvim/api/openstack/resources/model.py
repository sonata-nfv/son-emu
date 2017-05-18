class Model:
    def __init__(self, resources=None):
        if not resources:
            resources = list()
        self.resources = resources
