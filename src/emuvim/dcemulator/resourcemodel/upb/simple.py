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
        self.dc_alloc_mu = 0
        super(self.__class__, self).__init__()

    def allocate(self, name, flavor_name):
        """
        Calculate resources for container with given flavor.
        :param name: Container name.
        :param flavor_name: Flavor name.
        :return:
        """
        # bookkeeping and flavor handling
        if flavor_name not in self._flavors:
            raise Exception("Flavor %r does not exist" % flavor_name)
        fl = self._flavors.get(flavor_name)
        self.allocated_compute_instances[name] = flavor_name
        # calc and return
        return self._allocate_cpu(fl), self._allocate_mem(fl), -1.0  # return 3tuple (cpu, memory, disk)

    def free(self, name):
        """
        Free resources of given container.
        :param name: Container name.
        :return:
        """
        if name not in self.allocated_compute_instances:
            return False
        # bookkeeping
        self._free_cpu(self._flavors.get(self.allocated_compute_instances[name]))
        self._free_mem(self._flavors.get(self.allocated_compute_instances[name]))
        del self.allocated_compute_instances[name]
        # we don't have to calculate anything special here in this simple model
        return True

    def _allocate_cpu(self, flavor):
        """
        Allocate CPU time.
        :param flavor: flavor dict
        :return: cpu time fraction
        """
        fl_cu = flavor.get("compute")
        # check for over provisioning
        if self.dc_alloc_cu + fl_cu > self.dc_max_cu:
            raise Exception("Not enough compute resources left.")
        self.dc_alloc_cu += fl_cu
        # get cpu time fraction for entire emulation
        e_cpu = self.registrar.e_cpu
        # calculate cpu time fraction of a single compute unit
        cu = float(e_cpu) / sum([rm.dc_max_cu for rm in list(self.registrar.resource_models)])
        # calculate cpu time fraction for container with given flavor
        return cu * fl_cu

    def _free_cpu(self, flavor):
        """
        Free CPU allocation.
        :param flavor: flavor dict
        :return:
        """
        self.dc_alloc_cu -= flavor.get("compute")

    def _allocate_mem(self, flavor):
        """
        Allocate mem.
        :param flavor: flavor dict
        :return: mem limit in MB
        """
        fl_mu = flavor.get("memory")
        # check for over provisioning
        if self.dc_alloc_mu + fl_mu > self.dc_max_mu:
            raise Exception("Not enough memory resources left.")
        self.dc_alloc_mu += fl_mu
        # get cpu time fraction for entire emulation
        e_mem = self.registrar.e_mem
        # calculate cpu time fraction of a single compute unit
        mu = float(e_mem) / sum([rm.dc_max_mu for rm in list(self.registrar.resource_models)])
        # calculate cpu time fraction for container with given flavor
        return mu * fl_mu

    def _free_mem(self, flavor):
        """
        Free memory allocation
        :param flavor: flavor dict
        :return:
        """
        self.dc_alloc_mu -= flavor.get("memory")
