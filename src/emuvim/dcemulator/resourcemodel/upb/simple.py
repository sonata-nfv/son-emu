"""
Playground for resource models created by University of Paderborn.
"""
import logging
from emuvim.dcemulator.resourcemodel import BaseResourceModel

LOG = logging.getLogger("rm.upb.simple")
LOG.setLevel(logging.DEBUG)


class UpbSimpleCloudDcRM(BaseResourceModel):
    """
    This will be an example resource model that limits the overall
    resources that can be deployed per data center.
    No over provisioning. Resources are fixed throughout entire container
    lifetime.
    """

    def __init__(self, max_cu=32, max_mu=1024):
        """
        Initialize model.
        :param max_cu: Maximum number of compute units available in this DC.
        :param max_mu: Maximum memory of entire dc.
        :return:
        """
        self.dc_max_cu = max_cu
        self.dc_max_mu = max_mu
        self.dc_alloc_cu = 0
        super(self.__class__, self).__init__()

    def allocate(self, name, flavor_name):
        """
        Calculate resources for container with given flavor.
        :param name: Container name.
        :param flavor_name: Flavor name.
        :return:
        """
        # TODO Add memory model calculation (split in private methods for each tuple component)
        # bookkeeping and flavor handling
        if flavor_name not in self._flavors:
            raise Exception("Flavor %r does not exist" % flavor_name)
        fl = self._flavors.get(flavor_name)
        fl_cu = fl.get("compute")
        self.allocated_compute_instances[name] = flavor_name
        # check for over provisioning
        if self.dc_alloc_cu + fl_cu > self.dc_max_cu:
            raise Exception("Not enough compute resources left.")
        self.dc_alloc_cu += fl_cu
        #
        # calculate cpu limitation:
        #
        # get cpu time fraction for entire emulation
        e_cpu = self.registrar.e_cpu
        # calculate cpu time fraction of a single compute unit
        cu = e_cpu / sum([rm.dc_max_cu for rm in list(self.registrar.resource_models)])
        # calculate cpu time fraction for container with given flavor
        c_ct = cu * fl_cu
        return c_ct, -1.0, -1.0  # return 3tuple (cpu, memory, disk)

    def free(self, name):
        """
        Free resources of given container.
        :param name: Container name.
        :return:
        """
        if name not in self.allocated_compute_instances:
            return False
        # bookkeeping
        self.dc_alloc_cu -= self._flavors.get(self.allocated_compute_instances[name]).get("compute")
        del self.allocated_compute_instances[name]
        # we don't have to calculate anything special here in this simple model
        return True
