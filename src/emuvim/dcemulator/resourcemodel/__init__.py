"""
Base classes needed for resource models support.
"""

import logging
LOG = logging.getLogger("resourcemodel")
LOG.setLevel(logging.DEBUG)


class ResourceModelRegistrar(object):

    def __init__(self, dc_emulation_max_cpu):
        self.e_cpu = dc_emulation_max_cpu
        # pointer to all resource models assigned to DCs
        self._resource_models = dict()
        LOG.info("Resource model registrar created with dc_emulation_max_cpu=%r" % dc_emulation_max_cpu)

    def register(self, dc, rm):
        if dc in self._resource_models:
            raise Exception("There is already an resource model assigned to this DC.")
        self._resource_models[dc] = rm
        LOG.info("Registrar: Added resource model: %r" % rm)


class ResourceFlavor(object):

    def __init__(self, name, metrics):
        self.name = name
        self.metrics = metrics
        LOG.debug("Create flavor %r with metrics: %r" % (name, metrics))


class BaseResourceModel(object):

    def __init__(self):
        self._flavors=dict()
        self._initDefaultFlavors()
        LOG.info("Resource model %r initialized" % self)

    def __repr__(self):
        return self.__class__.__name__

    def _initDefaultFlavors(self):
        # initialize some default flavours (inspired by OpenStack)
        self.addFlavour(ResourceFlavor(
            "tiny",  {"compute": 1, "memory": 32, "disk": 1}))
        self.addFlavour(ResourceFlavor(
            "small",  {"compute": 4, "memory": 128, "disk": 20}))
        self.addFlavour(ResourceFlavor(
            "medium",  {"compute": 8, "memory": 256, "disk": 40}))
        self.addFlavour(ResourceFlavor(
            "large",  {"compute": 16, "memory": 512, "disk": 80}))
        self.addFlavour(ResourceFlavor(
            "xlarge",  {"compute": 32, "memory": 1024, "disk": 160}))

    def addFlavour(self, fl):
        if fl.name in self._flavors:
            raise Exception("Flavor with name %r already exists!" % fl.name)
        self._flavors[fl.name] = fl

    def allocate(self, name, flavor_name):
        LOG.info("RM-ALLOCATE: %r with flavor: %r" % (name, flavor_name))
        return 0.0, 0.0, 0.0

    def free(self, name):
        LOG.info("RM-FREE: %r" % name)

