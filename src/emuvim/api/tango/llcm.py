
# Copyright (c) 2018 SONATA-NFV, 5GTANGO and Paderborn University
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
# Neither the name of the SONATA-NFV, 5GTANGO, Paderborn University
# nor the names of its contributors may be used to endorse or promote
# products derived from this software without specific prior written
# permission.
#
# This work has been performed in the framework of the SONATA project,
# funded by the European Commission under Grant number 671517 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the SONATA
# partner consortium (www.sonata-nfv.eu).
#
# This work has also been performed in the framework of the 5GTANGO project,
# funded by the European Commission under Grant number 761493 through
# the Horizon 2020 and 5G-PPP programmes. The authors would like to
# acknowledge the contributions of their colleagues of the 5GTANGO
# partner consortium (www.5gtango.eu).
import logging
import os
import uuid
import hashlib
import zipfile
import yaml
import threading
import datetime
from docker import DockerClient
from flask import Flask, request
import flask_restful as fr
from gevent.pywsgi import WSGIServer
from subprocess import Popen
import ipaddress
import copy
import time


LOG = logging.getLogger("5gtango.llcm")
LOG.setLevel(logging.INFO)


CORS_HEADER = {'Access-Control-Allow-Origin': '*',
               'Access-Control-Allow-Methods': 'GET,OPTIONS'}


GK_STORAGE = "/tmp/vim-emu-tango-llcm/"
UPLOAD_FOLDER = os.path.join(GK_STORAGE, "uploads/")
CATALOG_FOLDER = os.path.join(GK_STORAGE, "catalog/")

# Enable Dockerfile build functionality
BUILD_DOCKERFILE = False

# flag to indicate that we run without the emulator (only the bare API for
# integration testing)
GK_STANDALONE_MODE = False

# should a new version of an image be pulled even if its available
FORCE_PULL = False

# flag to indicate if we use bidirectional forwarding rules in the
# automatic chaining process
BIDIRECTIONAL_CHAIN = True

# override the management interfaces in the descriptors with default
# docker0 interfaces in the containers
USE_DOCKER_MGMT = False

# automatically deploy uploaded packages (no need to execute son-access
# deploy --latest separately)
AUTO_DEPLOY = False

# and also automatically terminate any other running services
AUTO_DELETE = False

# global subnet definitions (see reset_subnets())
ELAN_SUBNETS = None
ELINE_SUBNETS = None

# Time in seconds to wait for vnf stop scripts to execute fully
VNF_STOP_WAIT_TIME = 5

# If services are instantiated multiple times, the public port
# mappings need to be adapted to avoid colisions. We use this
# offset for this: NEW_PORT (SSIID * OFFSET) + ORIGINAL_PORT
MULTI_INSTANCE_PORT_OFFSET = 1000

# Selected Placement Algorithm: Points to the class of the selected
# placement algorithm.
PLACEMENT_ALGORITHM_OBJ = None

# Path to folder with <container_name>.env.yml files that contain
# environment variables injected into the specific container
# when it is started.
PER_INSTANCE_ENV_CONFIGURATION_FOLDER = None


class OnBoardingException(BaseException):
    pass


class Gatekeeper(object):

    def __init__(self):
        self.services = dict()
        self.dcs = dict()
        self.net = None
        # used to generate short names for VNFs (Mininet limitation)
        self.vnf_counter = 0
        reset_subnets()
        LOG.info("Initialized 5GTANGO LLCM module.")

    def register_service_package(self, service_uuid, service):
        """
        register new service package
        :param service_uuid
        :param service object
        """
        self.services[service_uuid] = service
        # lets perform all steps needed to onboard the service
        service.onboard()


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
        self.local_docker_files = dict()
        self.remote_docker_image_urls = dict()
        self.instances = dict()
        self._instance_counter = 0
        self.created_at = str(datetime.datetime.now())

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
        if self.nsd is None:
            raise OnBoardingException("No NSD found.")
        if len(self.vnfds) < 1:
            raise OnBoardingException("No VNFDs found.")
        # 3. prepare container images (e.g. download or build Dockerfile)
        if BUILD_DOCKERFILE:
            self._load_docker_files()
            self._build_images_from_dockerfiles()
        else:
            self._load_docker_urls()
            self._pull_predefined_dockerimages()
        # 4. reserve subnets
        eline_fwd_links, elan_fwd_links = self._get_elines_and_elans()
        self.eline_subnets = [ELINE_SUBNETS.pop(0) for _ in eline_fwd_links]
        self.elan_subnets = [ELAN_SUBNETS.pop(0) for _ in elan_fwd_links]
        LOG.debug("Reserved subnets for service '{}': E-Line: {} / E-LAN: {}"
                  .format(self.manifest.get("name"),
                          self.eline_subnets, self.elan_subnets))
        LOG.info("On-boarded service: {}".format(self.manifest.get("name")))

    def start_service(self):
        """
        This methods creates and starts a new service instance.
        It computes placements, iterates over all VNFDs, and starts
        each VNFD as a Docker container in the data center selected
        by the placement algorithm.
        :return:
        """
        LOG.info("Starting service {} ({})"
                 .format(get_triple_id(self.nsd), self.uuid))

        # 1. each service instance gets a new uuid to identify it
        instance_uuid = str(uuid.uuid4())
        # build a instances dict (a bit like a NSR :))
        self.instances[instance_uuid] = dict()
        self.instances[instance_uuid]["uuid"] = self.uuid
        # SSIID = short service instance ID (to postfix Container names)
        self.instances[instance_uuid]["ssiid"] = self._instance_counter
        self.instances[instance_uuid]["name"] = get_triple_id(self.nsd)
        self.instances[instance_uuid]["vnf_instances"] = list()
        self.instances[instance_uuid]["created_at"] = str(datetime.datetime.now())
        # increase for next instance
        self._instance_counter += 1

        # 3. start all vnfds that we have in the service
        for vnf_id in self.vnfds:
            vnfd = self.vnfds[vnf_id]
            # attention: returns a list of started deployment units
            vnfis = self._start_vnfd(
                vnfd, vnf_id, self.instances[instance_uuid]["ssiid"])
            # add list of VNFIs to total VNFI list
            self.instances[instance_uuid]["vnf_instances"].extend(vnfis)

        # 4. Deploy E-Line, E-Tree and E-LAN links
        # Attention: Only done if ""forwarding_graphs" section in NSD exists,
        # even if "forwarding_graphs" are not used directly.
        # Attention2: Do a copy of *_subnets with list() is important here!
        eline_fwd_links, elan_fwd_links = self._get_elines_and_elans()
        # 5a. deploy E-Line links
        GK.net.deployed_elines.extend(eline_fwd_links)  # bookkeeping
        self._connect_elines(eline_fwd_links, instance_uuid, list(self.eline_subnets))
        # 5b. deploy E-Tree/E-LAN links
        GK.net.deployed_elans.extend(elan_fwd_links)  # bookkeeping
        self._connect_elans(elan_fwd_links, instance_uuid, list(self.elan_subnets))

        # 6. run the emulator specific entrypoint scripts in the VNFIs of this
        # service instance
        self._trigger_emulator_start_scripts_in_vnfis(
            self.instances[instance_uuid]["vnf_instances"])
        # done
        LOG.info("Service '{}' started. Instance id: {} SSIID: {}"
                 .format(self.instances[instance_uuid]["name"],
                         instance_uuid,
                         self.instances[instance_uuid]["ssiid"]))
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
        # stop all vnfs
        for v in vnf_instances:
            self._stop_vnfi(v)
        # last step: remove the instance from the list of all instances
        del self.instances[instance_uuid]

    def _get_elines_and_elans(self):
        """
        Get the E-Line, E-LAN, E-Tree links from the NSD.
        """
        # Attention: Only done if ""forwarding_graphs" section in NSD exists,
        # even if "forwarding_graphs" are not used directly.
        eline_fwd_links = list()
        elan_fwd_links = list()
        if "virtual_links" in self.nsd and "forwarding_graphs" in self.nsd:
            vlinks = self.nsd["virtual_links"]
            # constituent virtual links are not checked
            eline_fwd_links = [l for l in vlinks if (
                l["connectivity_type"] == "E-Line")]
            elan_fwd_links = [l for l in vlinks if (
                l["connectivity_type"] == "E-LAN" or
                l["connectivity_type"] == "E-Tree")]  # Treat E-Tree as E-LAN
        return eline_fwd_links, elan_fwd_links

    def _get_resource_limits(self, deployment_unit):
        """
        Extract resource limits from deployment units.
        """
        # defaults
        cpu_list = None
        cpu_period, cpu_quota = self._calculate_cpu_cfs_values(float(1.0))
        mem_limit = None
        # update from descriptor
        if "resource_requirements" in deployment_unit:
            res_req = deployment_unit.get("resource_requirements")
            cpu_list = res_req.get("cpu").get("cpuset")
            if cpu_list is None:
                cpu_list = res_req.get("cpu").get("vcpus")
            if cpu_list is not None:
                # attention: docker expects list as string w/o spaces:
                cpu_list = str(cpu_list).replace(" ", "").strip()
            cpu_bw = res_req.get("cpu").get("cpu_bw")
            if cpu_bw is None:
                cpu_bw = 1.0
            cpu_period, cpu_quota = self._calculate_cpu_cfs_values(float(cpu_bw))
            mem_limit = res_req.get("memory").get("size")
            mem_unit = str(res_req.get("memory").get("size_unit", "GB"))
            if mem_limit is not None:
                mem_limit = int(mem_limit)
                # to bytes
                if "G" in mem_unit:
                    mem_limit = mem_limit * 1024 * 1024 * 1024
                elif "M" in mem_unit:
                    mem_limit = mem_limit * 1024 * 1024
                elif "K" in mem_unit:
                    mem_limit = mem_limit * 1024
        return cpu_list, cpu_period, cpu_quota, mem_limit

    def _start_vnfd(self, vnfd, vnf_id, ssiid, **kwargs):
        """
        Start a single VNFD of this service
        :param vnfd: vnfd descriptor dict
        :param vnf_id: unique id of this vnf in the nsd
        :return:
        """
        vnfis = list()
        # the vnf_name refers to the container image to be deployed
        vnf_name = vnfd.get("name")
        # combine VDUs and CDUs
        deployment_units = (vnfd.get("virtual_deployment_units", []) +
                            vnfd.get("cloudnative_deployment_units", []))
        # iterate over all deployment units within each VNFDs
        for u in deployment_units:
            # 0. vnf_container_name = vnf_id.vdu_id
            vnf_container_name = get_container_name(vnf_id, u.get("id"))
            vnf_container_instance_name = get_container_name(vnf_id, u.get("id"), ssiid)
            # 1. get the name of the docker image to star
            if vnf_container_name not in self.remote_docker_image_urls:
                raise Exception("No image name for %r found. Abort." % vnf_container_name)
            docker_image_name = self.remote_docker_image_urls.get(vnf_container_name)
            # 2. select datacenter to start the VNF in
            target_dc = self._place(vnfd, vnf_id, u, ssiid)
            # 3. perform some checks to ensure we can start the container
            assert(docker_image_name is not None)
            assert(target_dc is not None)
            if not self._check_docker_image_exists(docker_image_name):
                raise Exception("Docker image {} not found. Abort."
                                .format(docker_image_name))

            # 4. get the resource limits
            cpu_list, cpu_period, cpu_quota, mem_limit = self._get_resource_limits(u)

            # get connection points defined for the DU
            intfs = u.get("connection_points", [])
            # do some re-naming of fields to be compatible to containernet
            for i in intfs:
                if i.get("address"):
                    i["ip"] = i.get("address")

            # get ports and port_bindings from the port and publish fields of CNFD
            # see: https://github.com/containernet/containernet/wiki/Exposing-and-mapping-network-ports
            ports = list()  # Containernet naming
            port_bindings = dict()
            for i in intfs:
                if i.get("port"):
                    if not isinstance(i.get("port"), int):
                        LOG.info("Field 'port' is no int CP: {}".format(i))
                    else:
                        ports.append(i.get("port"))
                if i.get("publish"):
                    if not isinstance(i.get("publish"), dict):
                        LOG.info("Field 'publish' is no dict CP: {}".format(i))
                    else:
                        port_bindings.update(i.get("publish"))
            # update port mapping for cases where service is deployed > 1 times
            port_bindings = update_port_mapping_multi_instance(ssiid, port_bindings)
            if len(ports) > 0:
                LOG.info("{} exposes ports: {}".format(vnf_container_instance_name, ports))
            if len(port_bindings) > 0:
                LOG.info("{} publishes ports: {}".format(vnf_container_instance_name, port_bindings))

            # 5. collect additional information to start container
            volumes = list()
            cenv = dict()
            # 5.1 inject descriptor based start/stop commands into env (overwrite)
            VNFD_CMD_START = u.get("vm_cmd_start")
            VNFD_CMD_STOP = u.get("vm_cmd_stop")
            if VNFD_CMD_START and not VNFD_CMD_START == "None":
                LOG.info("Found 'vm_cmd_start'='{}' in VNFD.".format(VNFD_CMD_START) +
                         " Overwriting SON_EMU_CMD.")
                cenv["SON_EMU_CMD"] = VNFD_CMD_START
            if VNFD_CMD_STOP and not VNFD_CMD_STOP == "None":
                LOG.info("Found 'vm_cmd_start'='{}' in VNFD.".format(VNFD_CMD_STOP) +
                         " Overwriting SON_EMU_CMD_STOP.")
                cenv["SON_EMU_CMD_STOP"] = VNFD_CMD_STOP

            # 5.2 inject per instance configurations based on envs
            conf_envs = self._load_instance_conf_envs(vnf_container_instance_name)
            cenv.update(conf_envs)

            # 6. Start the container
            LOG.info("Starting %r as %r in DC %r" %
                     (vnf_name, vnf_container_instance_name, target_dc))
            LOG.debug("Interfaces for %r: %r" % (vnf_id, intfs))
            # start the container
            vnfi = target_dc.startCompute(
                vnf_container_instance_name,
                network=intfs,
                image=docker_image_name,
                cpu_quota=cpu_quota,
                cpu_period=cpu_period,
                cpuset_cpus=cpu_list,
                mem_limit=mem_limit,
                volumes=volumes,
                properties=cenv,  # environment
                ports=ports,
                port_bindings=port_bindings,
                # only publish if explicitly stated in descriptor
                publish_all_ports=False,
                type=kwargs.get('type', 'docker'))
            # add vnfd reference to vnfi
            vnfi.vnfd = vnfd
            # add container name
            vnfi.vnf_container_name = vnf_container_name
            vnfi.vnf_container_instance_name = vnf_container_instance_name
            vnfi.ssiid = ssiid
            # store vnfi
            vnfis.append(vnfi)
        return vnfis

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
        Returns VNFI object for a given "vnf_id" or "vnf_container_name" taken from an NSD.
        :return: single object
        """
        for vnfi in self.instances[instance_uuid]["vnf_instances"]:
            if str(vnfi.name) == str(vnf_id):
                return vnfi
        LOG.warning("No container with name: {0} found.".format(vnf_id))
        return None

    def _get_vnf_instance_units(self, instance_uuid, vnf_id):
        """
        Returns a list of VNFI objects (all deployment units) for a given
        "vnf_id" taken from an NSD.
        :return: list
        """
        if vnf_id is None:
            return None
        r = list()
        for vnfi in self.instances[instance_uuid]["vnf_instances"]:
            if vnf_id in vnfi.name:
                r.append(vnfi)
        if len(r) > 0:
            LOG.debug("Found units: {} for vnf_id: {}"
                      .format([i.name for i in r], vnf_id))
            return r
        LOG.warning("No container(s) with name: {0} found.".format(vnf_id))
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
                if var == "SON_EMU_CMD" or var == "VIM_EMU_CMD":
                    LOG.info("Executing script in '{}': {}={}"
                             .format(vnfi.name, var, cmd))
                    # execute command in new thread to ensure that GK is not
                    # blocked by VNF
                    t = threading.Thread(target=vnfi.cmdPrint, args=(cmd,))
                    t.daemon = True
                    t.start()
                    break  # only execute one command

    def _trigger_emulator_stop_scripts_in_vnfis(self, vnfi_list):
        for vnfi in vnfi_list:
            config = vnfi.dcinfo.get("Config", dict())
            env = config.get("Env", list())
            for env_var in env:
                var, cmd = map(str.strip, map(str, env_var.split('=', 1)))
                if var == "SON_EMU_CMD_STOP" or var == "VIM_EMU_CMD_STOP":
                    LOG.info("Executing script in '{}': {}={}"
                             .format(vnfi.name, var, cmd))
                    # execute command in new thread to ensure that GK is not
                    # blocked by VNF
                    t = threading.Thread(target=vnfi.cmdPrint, args=(cmd,))
                    t.daemon = True
                    t.start()
                    break  # only execute one command

    def _load_instance_conf_envs(self, cname):
        """
        Try to load an instance-specific env file. If not found,
        just return an empty dict.
        """
        if PER_INSTANCE_ENV_CONFIGURATION_FOLDER is None:
            return dict()
        try:
            path = os.path.expanduser(PER_INSTANCE_ENV_CONFIGURATION_FOLDER)
            path = os.path.join(path, "{}.env.yml".format(cname))
            res = load_yaml(path)
            LOG.info("Loaded instance-specific env file for '{}': {}"
                     .format(cname, res))
            return res
        except BaseException as ex:
            LOG.info("No instance-specific env file found for: {}"
                     .format(cname))
            del ex
        return dict()

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
                self.package_content_path, "TOSCA-Metadata/NAPD.yaml"))

    def _load_nsd(self):
        """
        Load the entry NSD YAML and keep it as dict.
        :return:
        """
        if "package_content" in self.manifest:
            nsd_path = None
            for f in self.manifest.get("package_content"):
                if f.get("content-type") == "application/vnd.5gtango.nsd":
                    nsd_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(f.get("source")))
                    break  # always use the first NSD for now
            if nsd_path is None:
                raise OnBoardingException("No NSD with type 'application/vnd.5gtango.nsd' found.")
            self.nsd = load_yaml(nsd_path)
            GK.net.deployed_nsds.append(self.nsd)  # TODO this seems strange (remove?)
            LOG.debug("Loaded NSD: %r" % self.nsd.get("name"))
        else:
            raise OnBoardingException(
                "No 'package_content' section in package manifest:\n{}"
                .format(self.manifest))

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
                        "content-type") == "application/vnd.5gtango.vnfd":
                    vnfd_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(pc.get("source")))
                    vnfd = load_yaml(vnfd_path)
                    vnfd_set[vnfd.get("name")] = vnfd
            if len(vnfd_set) < 1:
                raise OnBoardingException("No VNFDs found.")
            # then link each vnf_id in the nsd to its vnfd
            for v in self.nsd.get("network_functions"):
                if v.get("vnf_name") in vnfd_set:
                    self.vnfds[v.get("vnf_id")] = vnfd_set[v.get("vnf_name")]
                LOG.debug("Loaded VNFD: {0} id: {1}"
                          .format(v.get("vnf_name"), v.get("vnf_id")))

    def _connect_elines(self, eline_fwd_links, instance_uuid, subnets):
        """
        Connect all E-LINE links in the NSD
        Attention: This method DOES NOT support multi V/CDU VNFs!
        :param eline_fwd_links: list of E-LINE links in the NSD
        :param: instance_uuid of the service
        :param: subnets list of subnets to be used
        :return:
        """
        # cookie is used as identifier for the flowrules installed by the dummygatekeeper
        # eg. different services get a unique cookie for their flowrules
        cookie = 1
        for link in eline_fwd_links:
            LOG.info("Found E-Line: {}".format(link))
            src_id, src_if_name = parse_interface(
                link["connection_points_reference"][0])
            dst_id, dst_if_name = parse_interface(
                link["connection_points_reference"][1])
            LOG.info("Searching C/VDU for E-Line: src={}, src_if={}, dst={}, dst_if={}"
                     .format(src_id, src_if_name, dst_id, dst_if_name))
            # handle C/VDUs (ugly hack, only one V/CDU per VNF for now)
            src_units = self._get_vnf_instance_units(instance_uuid, src_id)
            dst_units = self._get_vnf_instance_units(instance_uuid, dst_id)
            if src_units is None or dst_units is None:
                LOG.info("No VNF-VNF link. Skipping: src={}, src_if={}, dst={}, dst_if={}"
                         .format(src_id, src_if_name, dst_id, dst_if_name))
                return
            # we only support VNFs with one V/CDU right now
            if len(src_units) != 1 or len(dst_units) != 1:
                raise BaseException("LLCM does not support E-LINES for multi V/CDU VNFs.")
            # get the full name from that C/VDU and use it as src_id and dst_id
            src_id = src_units[0].name
            dst_id = dst_units[0].name
            # from here we have all info we need
            LOG.info("Creating E-Line for C/VDU: src={}, src_if={}, dst={}, dst_if={}"
                     .format(src_id, src_if_name, dst_id, dst_if_name))
            # get involved vnfis
            src_vnfi = src_units[0]
            dst_vnfi = dst_units[0]
            # proceed with chaining setup
            setChaining = False
            if src_vnfi is not None and dst_vnfi is not None:
                setChaining = True
                # re-configure the VNFs IP assignment and ensure that a new
                # subnet is used for each E-Link
                eline_net = subnets.pop(0)
                ip1 = "{0}/{1}".format(str(eline_net[1]),
                                       eline_net.prefixlen)
                ip2 = "{0}/{1}".format(str(eline_net[2]),
                                       eline_net.prefixlen)
                # check if VNFs have fixed IPs (ip/address field in VNFDs)
                if (self._get_vnfd_cp_from_vnfi(
                    src_vnfi, src_if_name).get("ip") is None and
                    self._get_vnfd_cp_from_vnfi(
                        src_vnfi, src_if_name).get("address") is None):
                    self._vnf_reconfigure_network(src_vnfi, src_if_name, ip1)
                # check if VNFs have fixed IPs (ip field in VNFDs)
                if (self._get_vnfd_cp_from_vnfi(
                    dst_vnfi, dst_if_name).get("ip") is None and
                    self._get_vnfd_cp_from_vnfi(
                        dst_vnfi, dst_if_name).get("address") is None):
                    self._vnf_reconfigure_network(dst_vnfi, dst_if_name, ip2)
            # set the chaining
            if setChaining:
                GK.net.setChain(
                    src_id, dst_id,
                    vnf_src_interface=src_if_name, vnf_dst_interface=dst_if_name,
                    bidirectional=BIDIRECTIONAL_CHAIN, cmd="add-flow", cookie=cookie, priority=10)

    def _get_vnfd_cp_from_vnfi(self, vnfi, ifname):
        """
        Gets the connection point data structure from the VNFD
        of the given VNFI using ifname.
        """
        if vnfi.vnfd is None:
            return {}
        cps = vnfi.vnfd.get("connection_points")
        for cp in cps:
            if cp.get("id") == ifname:
                return cp

    def _connect_elans(self, elan_fwd_links, instance_uuid, subnets):
        """
        Connect all E-LAN/E-Tree links in the NSD
        This method supports multi-V/CDU VNFs if the connection
        point names of the DUs are the same as the ones in the NSD.
        :param elan_fwd_links: list of E-LAN links in the NSD
        :param: instance_uuid of the service
        :param: subnets list of subnets to be used
        :return:
        """
        for link in elan_fwd_links:
            # a new E-LAN/E-Tree
            elan_vnf_list = []
            lan_net = subnets.pop(0)
            lan_hosts = list(lan_net.hosts())

            # generate lan ip address for all interfaces (of all involved (V/CDUs))
            for intf in link["connection_points_reference"]:
                vnf_id, intf_name = parse_interface(intf)
                if vnf_id is None:
                    continue  # skip references to NS connection points
                units = self._get_vnf_instance_units(instance_uuid, vnf_id)
                if units is None:
                    continue  # skip if no deployment unit is present
                # iterate over all involved deployment units
                for uvnfi in units:
                    # Attention: we apply a simplification for multi DU VNFs here:
                    # the connection points of all involved DUs have to have the same
                    # name as the connection points of the surrounding VNF to be mapped.
                    # This is because we do not consider links specified in the VNFds
                    container_name = uvnfi.name
                    ip_address = "{0}/{1}".format(str(lan_hosts.pop(0)),
                                                  lan_net.prefixlen)
                    LOG.debug(
                        "Setting up E-LAN/E-Tree interface. (%s:%s) -> %s" % (
                            container_name, intf_name, ip_address))
                    # re-configure the VNFs IP assignment and ensure that a new subnet is used for each E-LAN
                    # E-LAN relies on the learning switch capability of Ryu which has to be turned on in the topology
                    # (DCNetwork(controller=RemoteController, enable_learning=True)), so no explicit chaining is
                    # necessary.
                    vnfi = self._get_vnf_instance(instance_uuid, container_name)
                    if vnfi is not None:
                        self._vnf_reconfigure_network(vnfi, intf_name, ip_address)
                        # add this vnf and interface to the E-LAN for tagging
                        elan_vnf_list.append(
                            {'name': container_name, 'interface': intf_name})
            # install the VLAN tags for this E-LAN
            GK.net.setLAN(elan_vnf_list)

    def _load_docker_files(self):
        """
        Get all paths to Dockerfiles from VNFDs and store them in dict.
        :return:
        """
        for vnf_id, v in self.vnfds.iteritems():
            for vu in v.get("virtual_deployment_units", []):
                vnf_container_name = get_container_name(vnf_id, vu.get("id"))
                if vu.get("vm_image_format") == "docker":
                    vm_image = vu.get("vm_image")
                    docker_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(vm_image))
                    self.local_docker_files[vnf_container_name] = docker_path
                    LOG.debug("Found Dockerfile (%r): %r" % (vnf_container_name, docker_path))
            for cu in v.get("cloudnative_deployment_units", []):
                vnf_container_name = get_container_name(vnf_id, cu.get("id"))
                image = cu.get("image")
                docker_path = os.path.join(
                    self.package_content_path,
                    make_relative_path(image))
                self.local_docker_files[vnf_container_name] = docker_path
                LOG.debug("Found Dockerfile (%r): %r" % (vnf_container_name, docker_path))

    def _load_docker_urls(self):
        """
        Get all URLs to pre-build docker images in some repo.
        :return:
        """
        for vnf_id, v in self.vnfds.iteritems():
            for vu in v.get("virtual_deployment_units", []):
                vnf_container_name = get_container_name(vnf_id, vu.get("id"))
                if vu.get("vm_image_format") == "docker":
                    url = vu.get("vm_image")
                    if url is not None:
                        url = url.replace("http://", "")
                        self.remote_docker_image_urls[vnf_container_name] = url
                        LOG.debug("Found Docker image URL (%r): %r" %
                                  (vnf_container_name,
                                   self.remote_docker_image_urls[vnf_container_name]))
            for cu in v.get("cloudnative_deployment_units", []):
                vnf_container_name = get_container_name(vnf_id, cu.get("id"))
                url = cu.get("image")
                if url is not None:
                    url = url.replace("http://", "")
                    self.remote_docker_image_urls[vnf_container_name] = url
                    LOG.debug("Found Docker image URL (%r): %r" %
                              (vnf_container_name,
                               self.remote_docker_image_urls[vnf_container_name]))

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

    def _place(self, vnfd, vnfid, vdu, ssiid):
        """
        Do placement. Return the name of the DC to place
        the given VDU.
        """
        assert(len(self.vnfds) > 0)
        assert(len(GK.dcs) > 0)
        if PLACEMENT_ALGORITHM_OBJ is None:
            LOG.error("No placement algorithm given. Using FirstDcPlacement!")
            p = FirstDcPlacement()
        else:
            p = PLACEMENT_ALGORITHM_OBJ
        cname = get_container_name(vnfid, vdu.get("id"), ssiid)
        rdc = p.place(GK.dcs, vnfd, vnfid, vdu, ssiid, cname)
        LOG.info("Placement: '{}' --> '{}'".format(cname, rdc))
        return rdc

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


"""
Some (simple) placement algorithms
"""


class FirstDcPlacement(object):
    """
    Placement: Always use one and the same data center from the GK.dcs dict.
    """

    def place(self, dcs, vnfd, vnfid, vdu, ssiid, cname):
        return list(dcs.itervalues())[0]


class RoundRobinDcPlacement(object):
    """
    Placement: Distribute VNFs across all available DCs in a round robin fashion.
    """

    def __init__(self):
        self.count = 0

    def place(self, dcs, vnfd, vnfid, vdu, ssiid, cname):
        dcs_list = list(dcs.itervalues())
        rdc = dcs_list[self.count % len(dcs_list)]
        self.count += 1  # inc. count to use next DC
        return rdc


class StaticConfigPlacement(object):
    """
    Placement: Fixed assignment based on config file.
    """

    def __init__(self, path=None):
        if path is None:
            path = "static_placement.yml"
        path = os.path.expanduser(path)
        self.static_placement = dict()
        try:
            self.static_placement = load_yaml(path)
        except BaseException as ex:
            LOG.error(ex)
            LOG.error("Couldn't load placement from {}"
                      .format(path))
        LOG.info("Loaded static placement: {}"
                 .format(self.static_placement))

    def place(self, dcs, vnfd, vnfid, vdu, ssiid, cname):
        # check for container name entry
        if cname not in self.static_placement:
            LOG.error("Coudn't find {} in placement".format(cname))
            LOG.error("Using first DC as fallback!")
            return list(dcs.itervalues())[0]
        # lookup
        candidate_dc = self.static_placement.get(cname)
        # check if DC exsits
        if candidate_dc not in dcs:
            LOG.error("Coudn't find DC {}".format(candidate_dc))
            LOG.error("Using first DC as fallback!")
            return list(dcs.itervalues())[0]
        # return correct DC
        return dcs.get(candidate_dc)


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
            upload_path = os.path.join(UPLOAD_FOLDER, "%s.tgo" % service_uuid)
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
        Return a list of package descriptor headers.
        Fakes the behavior of 5GTANGO's GK API to be
        compatible with tng-cli.
        :return: list
        """
        LOG.info("GET /packages")
        result = list()
        for suuid, sobj in GK.services.iteritems():
            pkg = dict()
            pkg["pd"] = dict()
            pkg["uuid"] = suuid
            pkg["pd"]["name"] = sobj.manifest.get("name")
            pkg["pd"]["version"] = sobj.manifest.get("version")
            pkg["created_at"] = sobj.created_at
            result.append(pkg)
        return result, 200, CORS_HEADER


class Services(fr.Resource):

    def get(self):
        """
        Return a list of services.
        Fakes the behavior of 5GTANGO's GK API to be
        compatible with tng-cli.
        :return: list
        """
        LOG.info("GET /services")
        result = list()
        for suuid, sobj in GK.services.iteritems():
            service = dict()
            service["nsd"] = dict()
            service["uuid"] = suuid
            service["nsd"]["name"] = sobj.nsd.get("name")
            service["nsd"]["version"] = sobj.nsd.get("version")
            service["created_at"] = sobj.created_at
            result.append(service)
        return result, 200, CORS_HEADER


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
        service_name = json_data.get("service_name")
        if service_name is None:
            # lets be fuzzy
            service_name = service_uuid
        # first try to find by service_name
        if service_name is not None:
            for s_uuid, s in GK.services.iteritems():
                if s.manifest.get("name") == service_name:
                    LOG.info("Searched for: {}. Found service w. UUID: {}"
                             .format(service_name, s_uuid))
                    service_uuid = s_uuid
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
            # multiple ID fields to be compatible with tng-bench and tng-cli
            return ({"service_instance_uuid": service_instance_uuid,
                     "id": service_instance_uuid}, 201)
        LOG.error("Service not found: {}/{}".format(service_uuid, service_name))
        return "Service not found", 404

    def get(self):
        """
        Returns a list of UUIDs containing all running services.
        :return: dict / list
        """
        LOG.debug("GET /instantiations or /api/v3/records/services")
        # return {"service_instantiations_list": [
        #    list(s.instances.iterkeys()) for s in GK.services.itervalues()]}
        result = list()
        for suuid, sobj in GK.services.iteritems():
            for iuuid, iobj in sobj.instances.iteritems():
                inst = dict()
                inst["uuid"] = iobj.get("uuid")
                inst["instance_name"] = "{}-inst.{}".format(
                    iobj.get("name"), iobj.get("ssiid"))
                inst["status"] = "running"
                inst["created_at"] = iobj.get("created_at")
                result.append(inst)
        return result, 200, CORS_HEADER

    def delete(self):
        """
        Stops a running service specified by its service and instance UUID.
        """
        # try to extract the service  and instance UUID from the request
        json_data = request.get_json(force=True)
        service_uuid_input = json_data.get("service_uuid")
        instance_uuid_input = json_data.get("service_instance_uuid")
        if len(GK.services) < 1:
            return "No service on-boarded.", 404
        # try to be fuzzy
        if service_uuid_input is None:
            # if we don't get a service uuid we stop all services
            service_uuid_list = list(GK.services.iterkeys())
            LOG.info("No service_uuid given, stopping all.")
        else:
            service_uuid_list = [service_uuid_input]
        # for each service
        for service_uuid in service_uuid_list:
            if instance_uuid_input is None:
                instance_uuid_list = list(
                    GK.services[service_uuid].instances.iterkeys())
            else:
                instance_uuid_list = [instance_uuid_input]
            # for all service instances
            for instance_uuid in instance_uuid_list:
                if (service_uuid in GK.services and
                        instance_uuid in GK.services[service_uuid].instances):
                    # valid service and instance UUID, stop service
                    GK.services.get(service_uuid).stop_service(instance_uuid)
                    LOG.info("Service instance with uuid %r stopped." % instance_uuid)
        return "Service(s) stopped.", 200


class Exit(fr.Resource):

    def put(self):
        """
        Stop the running Containernet instance regardless of data transmitted
        """
        list(GK.dcs.values())[0].net.stop()


def generate_subnets(prefix, base, subnet_size=50, mask=24):
    # Generate a list of ipaddress in subnets
    r = list()
    for net in range(base, base + subnet_size):
        subnet = "{0}.{1}.0/{2}".format(prefix, net, mask)
        r.append(ipaddress.ip_network(unicode(subnet)))
    return r


def reset_subnets():
    global ELINE_SUBNETS
    global ELAN_SUBNETS
    # private subnet definitions for the generated interfaces
    # 30.0.xxx.0/24
    ELAN_SUBNETS = generate_subnets('30.0', 0, subnet_size=50, mask=24)
    # 20.0.xxx.0/24
    ELINE_SUBNETS = generate_subnets('20.0', 0, subnet_size=50, mask=24)


def initialize_GK():
    global GK
    GK = Gatekeeper()


# create a single, global GK object
GK = None
initialize_GK()
# setup Flask
http_server = None
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload
api = fr.Api(app)
# define endpoints
api.add_resource(Packages, '/packages', '/api/v2/packages', '/api/v3/packages')
api.add_resource(Services, '/services', '/api/v2/services', '/api/v3/services')
api.add_resource(Instantiations, '/instantiations',
                 '/api/v2/instantiations', '/api/v2/requests', '/api/v3/requests',
                 '/api/v3/records/services')
api.add_resource(Exit, '/emulator/exit')


def start_rest_api(host, port, datacenters=dict()):
    global http_server
    GK.dcs = datacenters
    GK.net = get_dc_network()
    # start the Flask server (not the best performance but ok for our use case)
    # app.run(host=host,
    #        port=port,
    #        debug=True,
    #        use_reloader=False  # this is needed to run Flask in a non-main thread
    #        )
    http_server = WSGIServer((host, port), app, log=open("/dev/null", "w"))
    http_server.serve_forever()


def stop_rest_api():
    if http_server:
        http_server.close()


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
    else:
        vnf_id = None
        vnf_interface = interface_name
    return vnf_id, vnf_interface


def get_container_name(vnf_id, vdu_id, ssiid=None):
    if ssiid is not None:
        return "{}.{}.{}".format(vnf_id, vdu_id, ssiid)
    return "{}.{}".format(vnf_id, vdu_id)


def get_triple_id(descr):
    return "{}.{}.{}".format(
        descr.get("vendor"), descr.get("name"), descr.get("version"))


def update_port_mapping_multi_instance(ssiid, port_bindings):
    """
    Port_bindings are used to expose ports of the deployed containers.
    They would collide if we deploy multiple service instances.
    This function adds a offset to them which is based on the
    short service instance id (SSIID).
    MULTI_INSTANCE_PORT_OFFSET
    """
    def _offset(p):
        return p + MULTI_INSTANCE_PORT_OFFSET * ssiid

    port_bindings = {k: _offset(v) for k, v in port_bindings.iteritems()}
    return port_bindings


if __name__ == '__main__':
    """
    Lets allow to run the API in standalone mode.
    """
    GK_STANDALONE_MODE = True
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    start_rest_api("0.0.0.0", 8000)
