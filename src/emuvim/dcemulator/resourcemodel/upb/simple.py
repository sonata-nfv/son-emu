# Copyright (c) 2015 SONATA-NFV and Paderborn University
# ALL RIGHTS RESERVED.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
# Neither the name of the SONATA-NFV, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
import time
import json
import logging
from emuvim.dcemulator.resourcemodel import BaseResourceModel, NotEnoughResourcesAvailable

LOG = logging.getLogger("rm.upb.simple")
LOG.setLevel(logging.DEBUG)

CPU_PERIOD = 1000000


class UpbSimpleCloudDcRM(BaseResourceModel):
    """
    This will be an example resource model that limits the overall
    resources that can be deployed per data center.
    No over provisioning. Resources are fixed throughout entire container
    lifetime.
    """

    def __init__(self, max_cu=32, max_mu=1024,
                 deactivate_cpu_limit=False,
                 deactivate_mem_limit=False):
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
        self.deactivate_cpu_limit = deactivate_cpu_limit
        self.deactivate_mem_limit = deactivate_mem_limit
        self.single_cu = 0
        self.single_mu = 0
        self.cpu_op_factor = 1.0  # over provisioning factor
        self.mem_op_factor = 1.0
        self.raise_no_cpu_resources_left = True
        self.raise_no_mem_resources_left = True
        super(UpbSimpleCloudDcRM, self).__init__()

    def allocate(self, d):
        """
        Allocate resources for the given container.
        Defined by d.flavor_name
        :param d: container
        :return:
        """
        self._allocated_compute_instances[d.name] = d
        if not self.deactivate_cpu_limit:
            self._allocate_cpu(d)
        if not self.deactivate_mem_limit:
            self._allocate_mem(d)
        self._apply_limits()

    def _allocate_cpu(self, d):
        """
        Actually allocate (bookkeeping)
        :param d: container
        :return:
        """
        fl_cu = self._get_flavor(d).get("compute")
        # check for over provisioning
        if self.dc_alloc_cu + fl_cu > self.dc_max_cu and self.raise_no_cpu_resources_left:
            raise NotEnoughResourcesAvailable(
                "Not enough compute resources left.")
        self.dc_alloc_cu += fl_cu

    def _allocate_mem(self, d):
        """
        Actually allocate (bookkeeping)
        :param d: container
        :return:
        """
        fl_mu = self._get_flavor(d).get("memory")
        # check for over provisioning
        if self.dc_alloc_mu + fl_mu > self.dc_max_mu and self.raise_no_mem_resources_left:
            raise NotEnoughResourcesAvailable(
                "Not enough memory resources left.")
        self.dc_alloc_mu += fl_mu

    def free(self, d):
        """
        Free resources allocated to the given container.
        :param d: container
        :return:
        """
        del self._allocated_compute_instances[d.name]
        if not self.deactivate_cpu_limit:
            self._free_cpu(d)
        if not self.deactivate_mem_limit:
            self._free_mem(d)
        self._apply_limits()

    def _free_cpu(self, d):
        """
        Free resources.
        :param d: container
        :return:
        """
        self.dc_alloc_cu -= self._get_flavor(d).get("compute")

    def _free_mem(self, d):
        """
        Free resources.
        :param d: container
        :return:
        """
        self.dc_alloc_mu -= self._get_flavor(d).get("memory")

    def _apply_limits(self):
        """
        Recalculate real resource limits for all allocated containers and apply them
        to their cgroups.
        We have to recalculate for all containers to allow e.g. over provisioning models.
        :return:
        """
        for d in self._allocated_compute_instances.values():
            if not self.deactivate_cpu_limit:
                self._apply_cpu_limits(d)
            if not self.deactivate_mem_limit:
                self._apply_mem_limits(d)

    def _apply_cpu_limits(self, d):
        """
        Calculate real CPU limit (CFS bandwidth) and apply.
        :param d: container
        :return:
        """
        number_cu = self._get_flavor(d).get("compute")
        # calculate cpu time fraction of a single compute unit
        self.single_cu = self._compute_single_cu()
        # calculate cpu time fraction for container with given flavor
        cpu_time_percentage = self.single_cu * number_cu
        # calculate input values for CFS scheduler bandwidth limitation
        cpu_period, cpu_quota = self._calculate_cpu_cfs_values(
            cpu_time_percentage)
        # apply limits to container if changed
        if d.resources['cpu_period'] != cpu_period or d.resources['cpu_quota'] != cpu_quota:
            LOG.debug("Setting CPU limit for %r: cpu_quota = cpu_period * limit = %f * %f = %f (op_factor=%f)" % (
                      d.name, cpu_period, cpu_time_percentage, cpu_quota, self.cpu_op_factor))
            d.updateCpuLimit(cpu_period=int(cpu_period),
                             cpu_quota=int(cpu_quota))

    def _compute_single_cu(self):
        """
        Calculate percentage of CPU time of a singe CU unit.
        :return:
        """
        # get cpu time fraction for entire emulation
        e_cpu = self.registrar.e_cpu
        # calculate
        return float(
            e_cpu) / sum([rm.dc_max_cu for rm in list(self.registrar.resource_models)])

    def _calculate_cpu_cfs_values(self, cpu_time_percentage):
        """
        Calculate cpu period and quota for CFS
        :param cpu_time_percentage: percentage of overall CPU to be used
        :return: cpu_period, cpu_quota
        """
        # (see: https://www.kernel.org/doc/Documentation/scheduler/sched-bwc.txt)
        # Attention minimum cpu_quota is 1ms (micro)
        cpu_period = CPU_PERIOD  # lets consider a fixed period of 1000000 microseconds for now
        # calculate the fraction of cpu time for this container
        cpu_quota = cpu_period * cpu_time_percentage
        # ATTENTION >= 1000 to avoid a invalid argument system error ... no
        # idea why
        if cpu_quota < 1000:
            cpu_quota = 1000
            LOG.warning("Increased CPU quota to avoid system error.")
        return cpu_period, cpu_quota

    def _apply_mem_limits(self, d):
        """
        Calculate real mem limit and apply.
        :param d: container
        :return:
        """
        number_mu = self._get_flavor(d).get("memory")
        # get memory amount for entire emulation
        e_mem = self.registrar.e_mem
        # calculate amount of memory for a single mu
        self.single_mu = float(
            e_mem) / sum([rm.dc_max_mu for rm in list(self.registrar.resource_models)])
        # calculate mem for given flavor
        mem_limit = self.single_mu * number_mu
        mem_limit = self._calculate_mem_limit_value(mem_limit)
        # apply to container if changed
        if d.resources['mem_limit'] != mem_limit:
            LOG.debug("Setting MEM limit for %r: mem_limit = %f MB (op_factor=%f)" %
                      (d.name, mem_limit / 1024 / 1024, self.mem_op_factor))
            d.updateMemoryLimit(mem_limit=mem_limit)

    def _calculate_mem_limit_value(self, mem_limit):
        """
        Calculate actual mem limit as input for cgroup API
        :param mem_limit: abstract mem limit
        :return: concrete mem limit
        """
        # ATTENTION minimum mem_limit per container is 4MB
        if mem_limit < 4:
            mem_limit = 4
            LOG.warning("Increased MEM limit because it was less than 4.0 MB.")
        # to byte!
        return int(mem_limit * 1024 * 1024)

    def get_state_dict(self):
        """
        Return the state of the resource model as simple dict.
        Helper method for logging functionality.
        :return:
        """
        # collect info about all allocated instances
        allocation_state = dict()
        for k, d in self._allocated_compute_instances.iteritems():
            s = dict()
            s["cpu_period"] = d.cpu_period
            s["cpu_quota"] = d.cpu_quota
            s["cpu_shares"] = d.cpu_shares
            s["mem_limit"] = d.mem_limit
            s["memswap_limit"] = d.memswap_limit
            allocation_state[k] = s
        # final result
        r = dict()
        r["e_cpu"] = self.registrar.e_cpu
        r["e_mem"] = self.registrar.e_mem
        r["dc_max_cu"] = self.dc_max_cu
        r["dc_max_mu"] = self.dc_max_mu
        r["dc_alloc_cu"] = self.dc_alloc_cu
        r["dc_alloc_mu"] = self.dc_alloc_mu
        r["single_cu_percentage"] = self.single_cu
        r["single_mu_percentage"] = self.single_mu
        r["cpu_op_factor"] = self.cpu_op_factor
        r["mem_op_factor"] = self.mem_op_factor
        r["allocation_state"] = allocation_state
        return r

    def _get_flavor(self, d):
        """
        Get flavor assigned to given container.
        Identified by d.flavor_name.
        :param d: container
        :return:
        """
        if d.flavor_name not in self._flavors:
            raise Exception("Flavor %r does not exist" % d.flavor_name)
        return self._flavors.get(d.flavor_name)

    def _write_log(self, d, path, action):
        """
        Helper to log RM info for experiments.
        :param d: container
        :param path: log path
        :param action: allocate or free
        :return:
        """
        if path is None:
            return
        # we have a path: write out RM info
        logd = dict()
        logd["t"] = time.time()
        logd["container_state"] = d.getStatus()
        logd["action"] = action
        logd["rm_state"] = self.get_state_dict()
        # append to logfile
        with open(path, "a") as f:
            f.write("%s\n" % json.dumps(logd))


class UpbOverprovisioningCloudDcRM(UpbSimpleCloudDcRM):
    """
    This will be an example resource model that limits the overall
    resources that can be deployed per data center.
    Allows over provisioning. Might result in reducing resources of single
    containers whenever a data-center is over provisioned.
    """
    # TODO add parts for memory

    def __init__(self, *args, **kvargs):
        super(UpbOverprovisioningCloudDcRM, self).__init__(*args, **kvargs)
        self.raise_no_cpu_resources_left = False

    def _compute_single_cu(self):
        """
        Calculate percentage of CPU time of a singe CU unit.
        Take scale-down facte for over provisioning into account.
        :return:
        """
        # get cpu time fraction for entire emulation
        e_cpu = self.registrar.e_cpu
        # calculate over provisioning scale factor
        self.cpu_op_factor = float(self.dc_max_cu) / \
            (max(self.dc_max_cu, self.dc_alloc_cu))
        # calculate
        return float(e_cpu) / sum([rm.dc_max_cu for rm in list(
            self.registrar.resource_models)]) * self.cpu_op_factor


class UpbDummyRM(UpbSimpleCloudDcRM):
    """
    No limits. But log allocations.
    """

    def __init__(self, *args, **kvargs):
        super(UpbDummyRM, self).__init__(*args, **kvargs)
        self.raise_no_cpu_resources_left = False

    def _apply_limits(self):
        # do nothing here
        pass
