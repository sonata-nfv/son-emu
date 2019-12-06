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
import logging
import os
import uuid
import hashlib
import zipfile
import yaml
import threading
from docker import DockerClient
from flask import Flask, request
import flask_restful as fr
from collections import defaultdict
import pkg_resources
from subprocess import Popen
from random import randint
import ipaddress
import copy
import time
from functools import reduce

logging.basicConfig()
LOG = logging.getLogger("sonata-dummy-gatekeeper")
LOG.setLevel(logging.DEBUG)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

GK_STORAGE = "/tmp/son-dummy-gk/"
UPLOAD_FOLDER = os.path.join(GK_STORAGE, "uploads/")
CATALOG_FOLDER = os.path.join(GK_STORAGE, "catalog/")

# Enable Dockerfile build functionality
BUILD_DOCKERFILE = False

# flag to indicate that we run without the emulator (only the bare API for
# integration testing)
GK_STANDALONE_MODE = False

# should a new version of an image be pulled even if its available
FORCE_PULL = False

# Automatically deploy SAPs (endpoints) of the service as new containers
# Attention: This is not a configuration switch but a global variable!
# Don't change its default value.
DEPLOY_SAP = False

# flag to indicate if we use bidirectional forwarding rules in the
# automatic chaining process
BIDIRECTIONAL_CHAIN = False

# override the management interfaces in the descriptors with default
# docker0 interfaces in the containers
USE_DOCKER_MGMT = False

# automatically deploy uploaded packages (no need to execute son-access
# deploy --latest separately)
AUTO_DEPLOY = False

# and also automatically terminate any other running services
AUTO_DELETE = False


def generate_subnets(prefix, base, subnet_size=50, mask=24):
    # Generate a list of ipaddress in subnets
    r = list()
    for net in range(base, base + subnet_size):
        subnet = "{0}.{1}.0/{2}".format(prefix, net, mask)
        r.append(ipaddress.ip_network(subnet))
    return r


# private subnet definitions for the generated interfaces
# 10.10.xxx.0/24
SAP_SUBNETS = generate_subnets('10.10', 0, subnet_size=50, mask=30)
# 10.20.xxx.0/30
ELAN_SUBNETS = generate_subnets('10.20', 0, subnet_size=50, mask=24)
# 10.30.xxx.0/30
ELINE_SUBNETS = generate_subnets('10.30', 0, subnet_size=50, mask=30)

# path to the VNFD for the SAP VNF that is deployed as internal SAP point
SAP_VNFD = None

# Time in seconds to wait for vnf stop scripts to execute fully
VNF_STOP_WAIT_TIME = 5


class Gatekeeper(object):

    def __init__(self):
        self.services = dict()
        self.dcs = dict()
        self.net = None
        # used to generate short names for VNFs (Mininet limitation)
        self.vnf_counter = 0
        LOG.info("Create SONATA dummy gatekeeper.")

    def register_service_package(self, service_uuid, service):
        """
        register new service package
        :param service_uuid
        :param service object
        """
        self.services[service_uuid] = service
        # lets perform all steps needed to onboard the service
        service.onboard()

    def get_next_vnf_name(self):
        self.vnf_counter += 1
        return "vnf%d" % self.vnf_counter


class Service(object):
    """
    This class represents a NS uploaded as a *.son package to the
    dummy gatekeeper.
    Can have multiple running instances of this service.
    """

    def __init__(self,
                 service_uuid,
                 package_file_hash,
                 package_file_path):
        self.uuid = service_uuid
        self.package_file_hash = package_file_hash
        self.package_file_path = package_file_path
        self.package_content_path = os.path.join(
            CATALOG_FOLDER, "services/%s" % self.uuid)
        self.manifest = None
        self.nsd = None
        self.vnfds = dict()
        self.saps = dict()
        self.saps_ext = list()
        self.saps_int = list()
        self.local_docker_files = dict()
        self.remote_docker_image_urls = dict()
        self.instances = dict()
        # dict to find the vnf_name for any vnf id
        self.vnf_id2vnf_name = dict()

    def onboard(self):
        """
        Do all steps to prepare this service to be instantiated
        :return:
        """
        # 1. extract the contents of the package and store them in our catalog
        self._unpack_service_package()
        # 2. read in all descriptor files
        self._load_package_descriptor()
        self._load_nsd()
        self._load_vnfd()
        if DEPLOY_SAP:
            self._load_saps()
        # 3. prepare container images (e.g. download or build Dockerfile)
        if BUILD_DOCKERFILE:
            self._load_docker_files()
            self._build_images_from_dockerfiles()
        else:
            self._load_docker_urls()
            self._pull_predefined_dockerimages()
        LOG.info("On-boarded service: %r" % self.manifest.get("name"))

    def start_service(self):
        """
        This methods creates and starts a new service instance.
        It computes placements, iterates over all VNFDs, and starts
        each VNFD as a Docker container in the data center selected
        by the placement algorithm.
        :return:
        """
        LOG.info("Starting service %r" % self.uuid)

        # 1. each service instance gets a new uuid to identify it
        instance_uuid = str(uuid.uuid4())
        # build a instances dict (a bit like a NSR :))
        self.instances[instance_uuid] = dict()
        self.instances[instance_uuid]["vnf_instances"] = list()

        # 2. compute placement of this service instance (adds DC names to
        # VNFDs)
        if not GK_STANDALONE_MODE:
            # self._calculate_placement(FirstDcPlacement)
            self._calculate_placement(RoundRobinDcPlacementWithSAPs)
        # 3. start all vnfds that we have in the service (except SAPs)
        for vnf_id in self.vnfds:
            vnfd = self.vnfds[vnf_id]
            vnfi = None
            if not GK_STANDALONE_MODE:
                vnfi = self._start_vnfd(vnfd, vnf_id)
            self.instances[instance_uuid]["vnf_instances"].append(vnfi)

        # 4. start all SAPs in the service
        for sap in self.saps:
            self._start_sap(self.saps[sap], instance_uuid)

        # 5. Deploy E-Line and E_LAN links
        # Attention: Only done if ""forwarding_graphs" section in NSD exists,
        # even if "forwarding_graphs" are not used directly.
        if "virtual_links" in self.nsd and "forwarding_graphs" in self.nsd:
            vlinks = self.nsd["virtual_links"]
            # constituent virtual links are not checked
            # fwd_links = self.nsd["forwarding_graphs"][0]["constituent_virtual_links"]
            eline_fwd_links = [l for l in vlinks if (
                l["connectivity_type"] == "E-Line")]
            elan_fwd_links = [l for l in vlinks if (
                l["connectivity_type"] == "E-LAN")]

            GK.net.deployed_elines.extend(eline_fwd_links)
            GK.net.deployed_elans.extend(elan_fwd_links)

            # 5a. deploy E-Line links
            self._connect_elines(eline_fwd_links, instance_uuid)

            # 5b. deploy E-LAN links
            self._connect_elans(elan_fwd_links, instance_uuid)

        # 6. run the emulator specific entrypoint scripts in the VNFIs of this
        # service instance
        self._trigger_emulator_start_scripts_in_vnfis(
            self.instances[instance_uuid]["vnf_instances"])

        LOG.info("Service started. Instance id: %r" % instance_uuid)
        return instance_uuid

    def stop_service(self, instance_uuid):
        """
        This method stops a running service instance.
        It iterates over all VNF instances, stopping them each
        and removing them from their data center.

        :param instance_uuid: the uuid of the service instance to be stopped
        """
        LOG.info("Stopping service %r" % self.uuid)
        # get relevant information
        # instance_uuid = str(self.uuid.uuid4())
        vnf_instances = self.instances[instance_uuid]["vnf_instances"]

        # trigger stop skripts in vnf instances and wait a few seconds for
        # completion
        self._trigger_emulator_stop_scripts_in_vnfis(vnf_instances)
        time.sleep(VNF_STOP_WAIT_TIME)

        for v in vnf_instances:
            self._stop_vnfi(v)

        for sap_name in self.saps_ext:
            ext_sap = self.saps[sap_name]
            target_dc = ext_sap.get("dc")
            target_dc.removeExternalSAP(sap_name)
            LOG.info("Stopping the SAP instance: %r in DC %r" %
                     (sap_name, target_dc))

        if not GK_STANDALONE_MODE:
            # remove placement?
            # self._remove_placement(RoundRobinPlacement)
            None

        # last step: remove the instance from the list of all instances
        del self.instances[instance_uuid]

    def _start_vnfd(self, vnfd, vnf_id, **kwargs):
        """
        Start a single VNFD of this service
        :param vnfd: vnfd descriptor dict
        :param vnf_id: unique id of this vnf in the nsd
        :return:
        """
        # the vnf_name refers to the container image to be deployed
        vnf_name = vnfd.get("name")

        # iterate over all deployment units within each VNFDs
        for u in vnfd.get("virtual_deployment_units"):
            # 1. get the name of the docker image to start and the assigned DC
            if vnf_id not in self.remote_docker_image_urls:
                raise Exception("No image name for %r found. Abort." % vnf_id)
            docker_name = self.remote_docker_image_urls.get(vnf_id)
            target_dc = vnfd.get("dc")
            # 2. perform some checks to ensure we can start the container
            assert(docker_name is not None)
            assert(target_dc is not None)
            if not self._check_docker_image_exists(docker_name):
                raise Exception(
                    "Docker image %r not found. Abort." % docker_name)

            # 3. get the resource limits
            res_req = u.get("resource_requirements")
            cpu_list = res_req.get("cpu").get("cores")
            if cpu_list is None:
                cpu_list = res_req.get("cpu").get("vcpus")
            if cpu_list is None:
                cpu_list = "1"
            cpu_bw = res_req.get("cpu").get("cpu_bw")
            if not cpu_bw:
                cpu_bw = 1
            mem_num = str(res_req.get("memory").get("size"))
            if len(mem_num) == 0:
                mem_num = "2"
            mem_unit = str(res_req.get("memory").get("size_unit"))
            if str(mem_unit) == 0:
                mem_unit = "GB"
            mem_limit = float(mem_num)
            if mem_unit == "GB":
                mem_limit = mem_limit * 1024 * 1024 * 1024
            elif mem_unit == "MB":
                mem_limit = mem_limit * 1024 * 1024
            elif mem_unit == "KB":
                mem_limit = mem_limit * 1024
            mem_lim = int(mem_limit)
            cpu_period, cpu_quota = self._calculate_cpu_cfs_values(
                float(cpu_bw))

            # check if we need to deploy the management ports
            intfs = vnfd.get("connection_points", [])
            mgmt_intf_names = []
            if USE_DOCKER_MGMT:
                mgmt_intfs = [vnf_id + ':' + intf['id']
                              for intf in intfs if intf.get('type') == 'management']
                # check if any of these management interfaces are used in a
                # management-type network in the nsd
                for nsd_intf_name in mgmt_intfs:
                    vlinks = [l["connection_points_reference"]
                              for l in self.nsd.get("virtual_links", [])]
                    for link in vlinks:
                        if nsd_intf_name in link and self.check_mgmt_interface(
                                link):
                            # this is indeed a management interface and can be
                            # skipped
                            vnf_id, vnf_interface, vnf_sap_docker_name = parse_interface(
                                nsd_intf_name)
                            found_interfaces = [
                                intf for intf in intfs if intf.get('id') == vnf_interface]
                            intfs.remove(found_interfaces[0])
                            mgmt_intf_names.append(vnf_interface)

            # 4. generate the volume paths for the docker container
            volumes = list()
            # a volume to extract log files
            docker_log_path = "/tmp/results/%s/%s" % (self.uuid, vnf_id)
            LOG.debug("LOG path for vnf %s is %s." % (vnf_id, docker_log_path))
            if not os.path.exists(docker_log_path):
                LOG.debug("Creating folder %s" % docker_log_path)
                os.makedirs(docker_log_path)

            volumes.append(docker_log_path + ":/mnt/share/")

            # 5. do the dc.startCompute(name="foobar") call to run the container
            # TODO consider flavors, and other annotations
            # TODO: get all vnf id's from the nsd for this vnfd and use those as dockername
            # use the vnf_id in the nsd as docker name
            # so deployed containers can be easily mapped back to the nsd
            LOG.info("Starting %r as %r in DC %r" %
                     (vnf_name, vnf_id, vnfd.get("dc")))
            LOG.debug("Interfaces for %r: %r" % (vnf_id, intfs))
            vnfi = target_dc.startCompute(
                vnf_id,
                network=intfs,
                image=docker_name,
                flavor_name="small",
                cpu_quota=cpu_quota,
                cpu_period=cpu_period,
                cpuset=cpu_list,
                mem_limit=mem_lim,
                volumes=volumes,
                type=kwargs.get('type', 'docker'))

            # rename the docker0 interfaces (eth0) to the management port name
            # defined in the VNFD
            if USE_DOCKER_MGMT:
                for intf_name in mgmt_intf_names:
                    self._vnf_reconfigure_network(
                        vnfi, 'eth0', new_name=intf_name)

            return vnfi

    def _stop_vnfi(self, vnfi):
        """
        Stop a VNF instance.

        :param vnfi: vnf instance to be stopped
        """
        # Find the correct datacenter
        status = vnfi.getStatus()
        dc = vnfi.datacenter

        # stop the vnfi
        LOG.info("Stopping the vnf instance contained in %r in DC %r" %
                 (status["name"], dc))
        dc.stopCompute(status["name"])

    def _get_vnf_instance(self, instance_uuid, vnf_id):
        """
        Returns the Docker object for the given VNF id (or Docker name).
        :param instance_uuid: UUID of the service instance to search in.
        :param name: VNF name or Docker name. We are fuzzy here.
        :return:
        """
        dn = vnf_id
        for vnfi in self.instances[instance_uuid]["vnf_instances"]:
            if vnfi.name == dn:
                return vnfi
        LOG.warning("No container with name: {0} found.".format(dn))
        return None

    @staticmethod
    def _vnf_reconfigure_network(vnfi, if_name, net_str=None, new_name=None):
        """
        Reconfigure the network configuration of a specific interface
        of a running container.
        :param vnfi: container instance
        :param if_name: interface name
        :param net_str: network configuration string, e.g., 1.2.3.4/24
        :return:
        """

        # assign new ip address
        if net_str is not None:
            intf = vnfi.intf(intf=if_name)
            if intf is not None:
                intf.setIP(net_str)
                LOG.debug("Reconfigured network of %s:%s to %r" %
                          (vnfi.name, if_name, net_str))
            else:
                LOG.warning("Interface not found: %s:%s. Network reconfiguration skipped." % (
                    vnfi.name, if_name))

        if new_name is not None:
            vnfi.cmd('ip link set', if_name, 'down')
            vnfi.cmd('ip link set', if_name, 'name', new_name)
            vnfi.cmd('ip link set', new_name, 'up')
            LOG.debug("Reconfigured interface name of %s:%s to %s" %
                      (vnfi.name, if_name, new_name))

    def _trigger_emulator_start_scripts_in_vnfis(self, vnfi_list):
        for vnfi in vnfi_list:
            config = vnfi.dcinfo.get("Config", dict())
            env = config.get("Env", list())
            for env_var in env:
                var, cmd = map(str.strip, map(str, env_var.split('=', 1)))
                LOG.debug("%r = %r" % (var, cmd))
                if var == "SON_EMU_CMD":
                    LOG.info("Executing entry point script in %r: %r" %
                             (vnfi.name, cmd))
                    # execute command in new thread to ensure that GK is not
                    # blocked by VNF
                    t = threading.Thread(target=vnfi.cmdPrint, args=(cmd,))
                    t.daemon = True
                    t.start()

    def _trigger_emulator_stop_scripts_in_vnfis(self, vnfi_list):
        for vnfi in vnfi_list:
            config = vnfi.dcinfo.get("Config", dict())
            env = config.get("Env", list())
            for env_var in env:
                var, cmd = map(str.strip, map(str, env_var.split('=', 1)))
                if var == "SON_EMU_CMD_STOP":
                    LOG.info("Executing stop script in %r: %r" %
                             (vnfi.name, cmd))
                    # execute command in new thread to ensure that GK is not
                    # blocked by VNF
                    t = threading.Thread(target=vnfi.cmdPrint, args=(cmd,))
                    t.daemon = True
                    t.start()

    def _unpack_service_package(self):
        """
        unzip *.son file and store contents in CATALOG_FOLDER/services/<service_uuid>/
        """
        LOG.info("Unzipping: %r" % self.package_file_path)
        with zipfile.ZipFile(self.package_file_path, "r") as z:
            z.extractall(self.package_content_path)

    def _load_package_descriptor(self):
        """
        Load the main package descriptor YAML and keep it as dict.
        :return:
        """
        self.manifest = load_yaml(
            os.path.join(
                self.package_content_path, "META-INF/MANIFEST.MF"))

    def _load_nsd(self):
        """
        Load the entry NSD YAML and keep it as dict.
        :return:
        """
        if "entry_service_template" in self.manifest:
            nsd_path = os.path.join(
                self.package_content_path,
                make_relative_path(self.manifest.get("entry_service_template")))
            self.nsd = load_yaml(nsd_path)
            GK.net.deployed_nsds.append(self.nsd)
            # create dict to find the vnf_name for any vnf id
            self.vnf_id2vnf_name = defaultdict(lambda: "NotExistingNode",
                                               reduce(lambda x, y: dict(x, **y),
                                                       map(lambda d: {d["vnf_id"]: d["vnf_name"]},
                                                           self.nsd["network_functions"])))

            LOG.debug("Loaded NSD: %r" % self.nsd.get("name"))

    def _load_vnfd(self):
        """
        Load all VNFD YAML files referenced in MANIFEST.MF and keep them in dict.
        :return:
        """

        # first make a list of all the vnfds in the package
        vnfd_set = dict()
        if "package_content" in self.manifest:
            for pc in self.manifest.get("package_content"):
                if pc.get(
                        "content-type") == "application/sonata.function_descriptor":
                    vnfd_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(pc.get("name")))
                    vnfd = load_yaml(vnfd_path)
                    vnfd_set[vnfd.get("name")] = vnfd
            # then link each vnf_id in the nsd to its vnfd
            for vnf_id in self.vnf_id2vnf_name:
                vnf_name = self.vnf_id2vnf_name[vnf_id]
                self.vnfds[vnf_id] = vnfd_set[vnf_name]
                LOG.debug("Loaded VNFD: {0} id: {1}".format(vnf_name, vnf_id))

    def _load_saps(self):
        # create list of all SAPs
        # check if we need to deploy management ports
        if USE_DOCKER_MGMT:
            SAPs = [p for p in self.nsd["connection_points"]
                    if 'management' not in p.get('type')]
        else:
            SAPs = [p for p in self.nsd["connection_points"]]

        for sap in SAPs:
            # endpoint needed in this service
            sap_id, sap_interface, sap_docker_name = parse_interface(sap['id'])
            # make sure SAP has type set (default internal)
            sap["type"] = sap.get("type", 'internal')

            # Each Service Access Point (connection_point) in the nsd is an IP
            # address on the host
            if sap["type"] == "external":
                # add to vnfds to calculate placement later on
                sap_net = SAP_SUBNETS.pop(0)
                self.saps[sap_docker_name] = {
                    "name": sap_docker_name, "type": "external", "net": sap_net}
                # add SAP vnf to list in the NSD so it is deployed later on
                # each SAP gets a unique VNFD and vnf_id in the NSD and custom
                # type (only defined in the dummygatekeeper)
                self.nsd["network_functions"].append(
                    {"vnf_id": sap_docker_name, "vnf_name": sap_docker_name, "vnf_type": "sap_ext"})

            # Each Service Access Point (connection_point) in the nsd is
            # getting its own container (default)
            elif sap["type"] == "internal" or sap["type"] == "management":
                # add SAP to self.vnfds
                if SAP_VNFD is None:
                    sapfile = pkg_resources.resource_filename(
                        __name__, "sap_vnfd.yml")
                else:
                    sapfile = SAP_VNFD
                sap_vnfd = load_yaml(sapfile)
                sap_vnfd["connection_points"][0]["id"] = sap_interface
                sap_vnfd["name"] = sap_docker_name
                sap_vnfd["type"] = "internal"
                # add to vnfds to calculate placement later on and deploy
                self.saps[sap_docker_name] = sap_vnfd
                # add SAP vnf to list in the NSD so it is deployed later on
                # each SAP get a unique VNFD and vnf_id in the NSD
                self.nsd["network_functions"].append(
                    {"vnf_id": sap_docker_name, "vnf_name": sap_docker_name, "vnf_type": "sap_int"})

            LOG.debug("Loaded SAP: name: {0}, type: {1}".format(
                sap_docker_name, sap['type']))

        # create sap lists
        self.saps_ext = [self.saps[sap]['name']
                         for sap in self.saps if self.saps[sap]["type"] == "external"]
        self.saps_int = [self.saps[sap]['name']
                         for sap in self.saps if self.saps[sap]["type"] == "internal"]

    def _start_sap(self, sap, instance_uuid):
        if not DEPLOY_SAP:
            return

        LOG.info('start SAP: {0} ,type: {1}'.format(sap['name'], sap['type']))
        if sap["type"] == "internal":
            vnfi = None
            if not GK_STANDALONE_MODE:
                vnfi = self._start_vnfd(sap, sap['name'], type='sap_int')
            self.instances[instance_uuid]["vnf_instances"].append(vnfi)

        elif sap["type"] == "external":
            target_dc = sap.get("dc")
            # add interface to dc switch
            target_dc.attachExternalSAP(sap['name'], sap['net'])

    def _connect_elines(self, eline_fwd_links, instance_uuid):
        """
        Connect all E-LINE links in the NSD
        :param eline_fwd_links: list of E-LINE links in the NSD
        :param: instance_uuid of the service
        :return:
        """
        # cookie is used as identifier for the flowrules installed by the dummygatekeeper
        # eg. different services get a unique cookie for their flowrules
        cookie = 1
        for link in eline_fwd_links:
            # check if we need to deploy this link when its a management link:
            if USE_DOCKER_MGMT:
                if self.check_mgmt_interface(
                        link["connection_points_reference"]):
                    continue

            src_id, src_if_name, src_sap_id = parse_interface(
                link["connection_points_reference"][0])
            dst_id, dst_if_name, dst_sap_id = parse_interface(
                link["connection_points_reference"][1])

            setChaining = False
            # check if there is a SAP in the link and chain everything together
            if src_sap_id in self.saps and dst_sap_id in self.saps:
                LOG.info(
                    '2 SAPs cannot be chained together : {0} - {1}'.format(src_sap_id, dst_sap_id))
                continue

            elif src_sap_id in self.saps_ext:
                src_id = src_sap_id
                # set intf name to None so the chaining function will choose
                # the first one
                src_if_name = None
                dst_vnfi = self._get_vnf_instance(instance_uuid, dst_id)
                if dst_vnfi is not None:
                    # choose first ip address in sap subnet
                    sap_net = self.saps[src_sap_id]['net']
                    sap_ip = "{0}/{1}".format(str(sap_net[2]),
                                              sap_net.prefixlen)
                    self._vnf_reconfigure_network(
                        dst_vnfi, dst_if_name, sap_ip)
                    setChaining = True

            elif dst_sap_id in self.saps_ext:
                dst_id = dst_sap_id
                # set intf name to None so the chaining function will choose
                # the first one
                dst_if_name = None
                src_vnfi = self._get_vnf_instance(instance_uuid, src_id)
                if src_vnfi is not None:
                    sap_net = self.saps[dst_sap_id]['net']
                    sap_ip = "{0}/{1}".format(str(sap_net[2]),
                                              sap_net.prefixlen)
                    self._vnf_reconfigure_network(
                        src_vnfi, src_if_name, sap_ip)
                    setChaining = True

            # Link between 2 VNFs
            else:
                # make sure we use the correct sap vnf name
                if src_sap_id in self.saps_int:
                    src_id = src_sap_id
                if dst_sap_id in self.saps_int:
                    dst_id = dst_sap_id
                # re-configure the VNFs IP assignment and ensure that a new
                # subnet is used for each E-Link
                src_vnfi = self._get_vnf_instance(instance_uuid, src_id)
                dst_vnfi = self._get_vnf_instance(instance_uuid, dst_id)
                if src_vnfi is not None and dst_vnfi is not None:
                    eline_net = ELINE_SUBNETS.pop(0)
                    ip1 = "{0}/{1}".format(str(eline_net[1]),
                                           eline_net.prefixlen)
                    ip2 = "{0}/{1}".format(str(eline_net[2]),
                                           eline_net.prefixlen)
                    self._vnf_reconfigure_network(src_vnfi, src_if_name, ip1)
                    self._vnf_reconfigure_network(dst_vnfi, dst_if_name, ip2)
                    setChaining = True

            # Set the chaining
            if setChaining:
                GK.net.setChain(
                    src_id, dst_id,
                    vnf_src_interface=src_if_name, vnf_dst_interface=dst_if_name,
                    bidirectional=BIDIRECTIONAL_CHAIN, cmd="add-flow", cookie=cookie, priority=10)
                LOG.debug(
                    "Setting up E-Line link. (%s:%s) -> (%s:%s)" % (
                        src_id, src_if_name, dst_id, dst_if_name))

    def _connect_elans(self, elan_fwd_links, instance_uuid):
        """
        Connect all E-LAN links in the NSD
        :param elan_fwd_links: list of E-LAN links in the NSD
        :param: instance_uuid of the service
        :return:
        """
        for link in elan_fwd_links:
            # check if we need to deploy this link when its a management link:
            if USE_DOCKER_MGMT:
                if self.check_mgmt_interface(
                        link["connection_points_reference"]):
                    continue

            elan_vnf_list = []
            # check if an external SAP is in the E-LAN (then a subnet is
            # already defined)
            intfs_elan = [intf for intf in link["connection_points_reference"]]
            lan_sap = self.check_ext_saps(intfs_elan)
            if lan_sap:
                lan_net = self.saps[lan_sap]['net']
                lan_hosts = list(lan_net.hosts())
            else:
                lan_net = ELAN_SUBNETS.pop(0)
                lan_hosts = list(lan_net.hosts())

            # generate lan ip address for all interfaces except external SAPs
            for intf in link["connection_points_reference"]:

                # skip external SAPs, they already have an ip
                vnf_id, vnf_interface, vnf_sap_docker_name = parse_interface(
                    intf)
                if vnf_sap_docker_name in self.saps_ext:
                    elan_vnf_list.append(
                        {'name': vnf_sap_docker_name, 'interface': vnf_interface})
                    continue

                ip_address = "{0}/{1}".format(str(lan_hosts.pop(0)),
                                              lan_net.prefixlen)
                vnf_id, intf_name, vnf_sap_id = parse_interface(intf)

                # make sure we use the correct sap vnf name
                src_docker_name = vnf_id
                if vnf_sap_id in self.saps_int:
                    src_docker_name = vnf_sap_id
                    vnf_id = vnf_sap_id

                LOG.debug(
                    "Setting up E-LAN interface. (%s:%s) -> %s" % (
                        vnf_id, intf_name, ip_address))

                # re-configure the VNFs IP assignment and ensure that a new subnet is used for each E-LAN
                # E-LAN relies on the learning switch capability of Ryu which has to be turned on in the topology
                # (DCNetwork(controller=RemoteController, enable_learning=True)), so no explicit chaining is necessary.
                vnfi = self._get_vnf_instance(instance_uuid, vnf_id)
                if vnfi is not None:
                    self._vnf_reconfigure_network(vnfi, intf_name, ip_address)
                    # add this vnf and interface to the E-LAN for tagging
                    elan_vnf_list.append(
                        {'name': src_docker_name, 'interface': intf_name})

            # install the VLAN tags for this E-LAN
            GK.net.setLAN(elan_vnf_list)

    def _load_docker_files(self):
        """
        Get all paths to Dockerfiles from VNFDs and store them in dict.
        :return:
        """
        for k, v in self.vnfds.iteritems():
            for vu in v.get("virtual_deployment_units"):
                if vu.get("vm_image_format") == "docker":
                    vm_image = vu.get("vm_image")
                    docker_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(vm_image))
                    self.local_docker_files[k] = docker_path
                    LOG.debug("Found Dockerfile (%r): %r" % (k, docker_path))

    def _load_docker_urls(self):
        """
        Get all URLs to pre-build docker images in some repo.
        :return:
        """
        # also merge sap dicts, because internal saps also need a docker
        # container
        all_vnfs = self.vnfds.copy()
        all_vnfs.update(self.saps)

        for k, v in all_vnfs.iteritems():
            for vu in v.get("virtual_deployment_units", {}):
                if vu.get("vm_image_format") == "docker":
                    url = vu.get("vm_image")
                    if url is not None:
                        url = url.replace("http://", "")
                        self.remote_docker_image_urls[k] = url
                        LOG.debug("Found Docker image URL (%r): %r" %
                                  (k, self.remote_docker_image_urls[k]))

    def _build_images_from_dockerfiles(self):
        """
        Build Docker images for each local Dockerfile found in the package: self.local_docker_files
        """
        if GK_STANDALONE_MODE:
            return  # do not build anything in standalone mode
        dc = DockerClient()
        LOG.info("Building %d Docker images (this may take several minutes) ..." % len(
            self.local_docker_files))
        for k, v in self.local_docker_files.iteritems():
            for line in dc.build(path=v.replace(
                    "Dockerfile", ""), tag=k, rm=False, nocache=False):
                LOG.debug("DOCKER BUILD: %s" % line)
            LOG.info("Docker image created: %s" % k)

    def _pull_predefined_dockerimages(self):
        """
        If the package contains URLs to pre-build Docker images, we download them with this method.
        """
        dc = DockerClient()
        for url in self.remote_docker_image_urls.itervalues():
            # only pull if not present (speedup for development)
            if not FORCE_PULL:
                if len(dc.images.list(name=url)) > 0:
                    LOG.debug("Image %r present. Skipping pull." % url)
                    continue
            LOG.info("Pulling image: %r" % url)
            # this seems to fail with latest docker api version 2.0.2
            # dc.images.pull(url,
            #        insecure_registry=True)
            # using docker cli instead
            cmd = ["docker",
                   "pull",
                   url,
                   ]
            Popen(cmd).wait()

    def _check_docker_image_exists(self, image_name):
        """
        Query the docker service and check if the given image exists
        :param image_name: name of the docker image
        :return:
        """
        return len(DockerClient().images.list(name=image_name)) > 0

    def _calculate_placement(self, algorithm):
        """
        Do placement by adding the a field "dc" to
        each VNFD that points to one of our
        data center objects known to the gatekeeper.
        """
        assert(len(self.vnfds) > 0)
        assert(len(GK.dcs) > 0)
        # instantiate algorithm an place
        p = algorithm()
        p.place(self.nsd, self.vnfds, self.saps, GK.dcs)
        LOG.info("Using placement algorithm: %r" % p.__class__.__name__)
        # lets print the placement result
        for name, vnfd in self.vnfds.iteritems():
            LOG.info("Placed VNF %r on DC %r" % (name, str(vnfd.get("dc"))))
        for sap in self.saps:
            sap_dict = self.saps[sap]
            LOG.info("Placed SAP %r on DC %r" % (sap, str(sap_dict.get("dc"))))

    def _calculate_cpu_cfs_values(self, cpu_time_percentage):
        """
        Calculate cpu period and quota for CFS
        :param cpu_time_percentage: percentage of overall CPU to be used
        :return: cpu_period, cpu_quota
        """
        if cpu_time_percentage is None:
            return -1, -1
        if cpu_time_percentage < 0:
            return -1, -1
        # (see: https://www.kernel.org/doc/Documentation/scheduler/sched-bwc.txt)
        # Attention minimum cpu_quota is 1ms (micro)
        cpu_period = 1000000  # lets consider a fixed period of 1000000 microseconds for now
        LOG.debug("cpu_period is %r, cpu_percentage is %r" %
                  (cpu_period, cpu_time_percentage))
        # calculate the fraction of cpu time for this container
        cpu_quota = cpu_period * cpu_time_percentage
        # ATTENTION >= 1000 to avoid a invalid argument system error ... no
        # idea why
        if cpu_quota < 1000:
            LOG.debug("cpu_quota before correcting: %r" % cpu_quota)
            cpu_quota = 1000
            LOG.warning("Increased CPU quota to avoid system error.")
        LOG.debug("Calculated: cpu_period=%f / cpu_quota=%f" %
                  (cpu_period, cpu_quota))
        return int(cpu_period), int(cpu_quota)

    def check_ext_saps(self, intf_list):
        # check if the list of interfacs contains an external SAP
        saps_ext = [self.saps[sap]['name']
                    for sap in self.saps if self.saps[sap]["type"] == "external"]
        for intf_name in intf_list:
            vnf_id, vnf_interface, vnf_sap_docker_name = parse_interface(
                intf_name)
            if vnf_sap_docker_name in saps_ext:
                return vnf_sap_docker_name

    def check_mgmt_interface(self, intf_list):
        SAPs_mgmt = [p.get('id') for p in self.nsd["connection_points"]
                     if 'management' in p.get('type')]
        for intf_name in intf_list:
            if intf_name in SAPs_mgmt:
                return True


"""
Some (simple) placement algorithms
"""


class FirstDcPlacement(object):
    """
    Placement: Always use one and the same data center from the GK.dcs dict.
    """

    def place(self, nsd, vnfds, saps, dcs):
        for id, vnfd in vnfds.iteritems():
            vnfd["dc"] = list(dcs.itervalues())[0]


class RoundRobinDcPlacement(object):
    """
    Placement: Distribute VNFs across all available DCs in a round robin fashion.
    """

    def place(self, nsd, vnfds, saps, dcs):
        c = 0
        dcs_list = list(dcs.itervalues())
        for id, vnfd in vnfds.iteritems():
            vnfd["dc"] = dcs_list[c % len(dcs_list)]
            c += 1  # inc. c to use next DC


class RoundRobinDcPlacementWithSAPs(object):
    """
    Placement: Distribute VNFs across all available DCs in a round robin fashion,
    every SAP is instantiated on the same DC as the connected VNF.
    """

    def place(self, nsd, vnfds, saps, dcs):

        # place vnfs
        c = 0
        dcs_list = list(dcs.itervalues())
        for id, vnfd in vnfds.iteritems():
            vnfd["dc"] = dcs_list[c % len(dcs_list)]
            c += 1  # inc. c to use next DC

        # place SAPs
        vlinks = nsd.get("virtual_links", [])
        eline_fwd_links = [l for l in vlinks if (
            l["connectivity_type"] == "E-Line")]
        elan_fwd_links = [l for l in vlinks if (
            l["connectivity_type"] == "E-LAN")]

        # SAPs on E-Line links are placed on the same DC as the VNF on the
        # E-Line
        for link in eline_fwd_links:
            src_id, src_if_name, src_sap_id = parse_interface(
                link["connection_points_reference"][0])
            dst_id, dst_if_name, dst_sap_id = parse_interface(
                link["connection_points_reference"][1])

            # check if there is a SAP in the link
            if src_sap_id in saps:
                # get dc where connected vnf is mapped to
                dc = vnfds[dst_id]['dc']
                saps[src_sap_id]['dc'] = dc

            if dst_sap_id in saps:
                # get dc where connected vnf is mapped to
                dc = vnfds[src_id]['dc']
                saps[dst_sap_id]['dc'] = dc

        # SAPs on E-LANs are placed on a random DC
        dcs_list = list(dcs.itervalues())
        dc_len = len(dcs_list)
        for link in elan_fwd_links:
            for intf in link["connection_points_reference"]:
                # find SAP interfaces
                intf_id, intf_name, intf_sap_id = parse_interface(intf)
                if intf_sap_id in saps:
                    dc = dcs_list[randint(0, dc_len - 1)]
                    saps[intf_sap_id]['dc'] = dc


"""
Resource definitions and API endpoints
"""


class Packages(fr.Resource):

    def post(self):
        """
        Upload a *.son service package to the dummy gatekeeper.

        We expect request with a *.son file and store it in UPLOAD_FOLDER
        :return: UUID
        """
        try:
            # get file contents
            LOG.info("POST /packages called")
            # lets search for the package in the request
            is_file_object = False  # make API more robust: file can be in data or in files field
            if "package" in request.files:
                son_file = request.files["package"]
                is_file_object = True
            elif len(request.data) > 0:
                son_file = request.data
            else:
                return {"service_uuid": None, "size": 0, "sha1": None,
                        "error": "upload failed. file not found."}, 500
            # generate a uuid to reference this package
            service_uuid = str(uuid.uuid4())
            file_hash = hashlib.sha1(str(son_file)).hexdigest()
            # ensure that upload folder exists
            ensure_dir(UPLOAD_FOLDER)
            upload_path = os.path.join(UPLOAD_FOLDER, "%s.son" % service_uuid)
            # store *.son file to disk
            if is_file_object:
                son_file.save(upload_path)
            else:
                with open(upload_path, 'wb') as f:
                    f.write(son_file)
            size = os.path.getsize(upload_path)

            # first stop and delete any other running services
            if AUTO_DELETE:
                service_list = copy.copy(GK.services)
                for service_uuid in service_list:
                    instances_list = copy.copy(
                        GK.services[service_uuid].instances)
                    for instance_uuid in instances_list:
                        # valid service and instance UUID, stop service
                        GK.services.get(service_uuid).stop_service(
                            instance_uuid)
                        LOG.info("service instance with uuid %r stopped." %
                                 instance_uuid)

            # create a service object and register it
            s = Service(service_uuid, file_hash, upload_path)
            GK.register_service_package(service_uuid, s)

            # automatically deploy the service
            if AUTO_DEPLOY:
                # ok, we have a service uuid, lets start the service
                reset_subnets()
                GK.services.get(service_uuid).start_service()

            # generate the JSON result
            return {"service_uuid": service_uuid, "size": size,
                    "sha1": file_hash, "error": None}, 201
        except BaseException:
            LOG.exception("Service package upload failed:")
            return {"service_uuid": None, "size": 0,
                    "sha1": None, "error": "upload failed"}, 500

    def get(self):
        """
        Return a list of UUID's of uploaded service packages.
        :return: dict/list
        """
        LOG.info("GET /packages")
        return {"service_uuid_list": list(GK.services.iterkeys())}


class Instantiations(fr.Resource):

    def post(self):
        """
        Instantiate a service specified by its UUID.
        Will return a new UUID to identify the running service instance.
        :return: UUID
        """
        LOG.info("POST /instantiations (or /requests) called")
        # try to extract the service uuid from the request
        json_data = request.get_json(force=True)
        service_uuid = json_data.get("service_uuid")

        # lets be a bit fuzzy here to make testing easier
        if (service_uuid is None or service_uuid ==
                "latest") and len(GK.services) > 0:
            # if we don't get a service uuid, we simple start the first service
            # in the list
            service_uuid = list(GK.services.iterkeys())[0]
        if service_uuid in GK.services:
            # ok, we have a service uuid, lets start the service
            service_instance_uuid = GK.services.get(
                service_uuid).start_service()
            return {"service_instance_uuid": service_instance_uuid}, 201
        return "Service not found", 404

    def get(self):
        """
        Returns a list of UUIDs containing all running services.
        :return: dict / list
        """
        LOG.info("GET /instantiations")
        return {"service_instantiations_list": [
            list(s.instances.iterkeys()) for s in GK.services.itervalues()]}

    def delete(self):
        """
        Stops a running service specified by its service and instance UUID.
        """
        # try to extract the service  and instance UUID from the request
        json_data = request.get_json(force=True)
        service_uuid = json_data.get("service_uuid")
        instance_uuid = json_data.get("service_instance_uuid")

        # try to be fuzzy
        if service_uuid is None and len(GK.services) > 0:
            # if we don't get a service uuid, we simply stop the last service
            # in the list
            service_uuid = list(GK.services.iterkeys())[0]
        if instance_uuid is None and len(
                GK.services[service_uuid].instances) > 0:
            instance_uuid = list(
                GK.services[service_uuid].instances.iterkeys())[0]

        if service_uuid in GK.services and instance_uuid in GK.services[service_uuid].instances:
            # valid service and instance UUID, stop service
            GK.services.get(service_uuid).stop_service(instance_uuid)
            return "service instance with uuid %r stopped." % instance_uuid, 200
        return "Service not found", 404


class Exit(fr.Resource):

    def put(self):
        """
        Stop the running Containernet instance regardless of data transmitted
        """
        list(GK.dcs.values())[0].net.stop()


def initialize_GK():
    global GK
    GK = Gatekeeper()


# create a single, global GK object
GK = None
initialize_GK()
# setup Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload
api = fr.Api(app)
# define endpoints
api.add_resource(Packages, '/packages', '/api/v2/packages')
api.add_resource(Instantiations, '/instantiations',
                 '/api/v2/instantiations', '/api/v2/requests')
api.add_resource(Exit, '/emulator/exit')


def start_rest_api(host, port, datacenters=dict()):
    GK.dcs = datacenters
    GK.net = get_dc_network()
    # start the Flask server (not the best performance but ok for our use case)
    app.run(host=host,
            port=port,
            debug=True,
            use_reloader=False  # this is needed to run Flask in a non-main thread
            )


def ensure_dir(name):
    if not os.path.exists(name):
        os.makedirs(name)


def load_yaml(path):
    with open(path, "r") as f:
        try:
            r = yaml.load(f)
        except yaml.YAMLError as exc:
            LOG.exception("YAML parse error: %r" % str(exc))
            r = dict()
    return r


def make_relative_path(path):
    if path.startswith("file://"):
        path = path.replace("file://", "", 1)
    if path.startswith("/"):
        path = path.replace("/", "", 1)
    return path


def get_dc_network():
    """
    retrieve the DCnetwork where this dummygatekeeper (GK) connects to.
    Assume at least 1 datacenter is connected to this GK, and that all datacenters belong to the same DCNetwork
    :return:
    """
    assert (len(GK.dcs) > 0)
    return GK.dcs.values()[0].net


def parse_interface(interface_name):
    """
    convert the interface name in the nsd to the according vnf_id, vnf_interface names
    :param interface_name:
    :return:
    """

    if ':' in interface_name:
        vnf_id, vnf_interface = interface_name.split(':')
        vnf_sap_docker_name = interface_name.replace(':', '_')
    else:
        vnf_id = interface_name
        vnf_interface = interface_name
        vnf_sap_docker_name = interface_name

    return vnf_id, vnf_interface, vnf_sap_docker_name


def reset_subnets():
    # private subnet definitions for the generated interfaces
    # 10.10.xxx.0/24
    global SAP_SUBNETS
    SAP_SUBNETS = generate_subnets('10.10', 0, subnet_size=50, mask=30)
    # 10.20.xxx.0/30
    global ELAN_SUBNETS
    ELAN_SUBNETS = generate_subnets('10.20', 0, subnet_size=50, mask=24)
    # 10.30.xxx.0/30
    global ELINE_SUBNETS
    ELINE_SUBNETS = generate_subnets('10.30', 0, subnet_size=50, mask=30)


if __name__ == '__main__':
    """
    Lets allow to run the API in standalone mode.
    """
    GK_STANDALONE_MODE = True
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    start_rest_api("0.0.0.0", 8000)
