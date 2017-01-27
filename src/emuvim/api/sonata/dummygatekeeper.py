"""
Copyright (c) 2015 SONATA-NFV and Paderborn University
ALL RIGHTS RESERVED.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

Neither the name of the SONATA-NFV [, ANY ADDITIONAL AFFILIATION]
nor the names of its contributors may be used to endorse or promote
products derived from this software without specific prior written
permission.

This work has been performed in the framework of the SONATA project,
funded by the European Commission under Grant number 671517 through
the Horizon 2020 and 5G-PPP programmes. The authors would like to
acknowledge the contributions of their colleagues of the SONATA
partner consortium (www.sonata-nfv.eu).
"""
"""
This module implements a simple REST API that behaves like SONATA's gatekeeper.

It is only used to support the development of SONATA's SDK tools and to demonstrate
the year 1 version of the emulator until the integration with WP4's orchestrator is done.
"""

import logging
import os
import uuid
import hashlib
import zipfile
import yaml
import threading
from docker import DockerClient, APIClient
from flask import Flask, request
import flask_restful as fr
from collections import defaultdict
import pkg_resources
from subprocess import Popen

logging.basicConfig()
LOG = logging.getLogger("sonata-dummy-gatekeeper")
LOG.setLevel(logging.DEBUG)
logging.getLogger("werkzeug").setLevel(logging.WARNING)

GK_STORAGE = "/tmp/son-dummy-gk/"
UPLOAD_FOLDER = os.path.join(GK_STORAGE, "uploads/")
CATALOG_FOLDER = os.path.join(GK_STORAGE, "catalog/")

# Enable Dockerfile build functionality
BUILD_DOCKERFILE = False

# flag to indicate that we run without the emulator (only the bare API for integration testing)
GK_STANDALONE_MODE = False

# should a new version of an image be pulled even if its available
FORCE_PULL = False

# Automatically deploy SAPs (endpoints) of the service as new containers
# Attention: This is not a configuration switch but a global variable! Don't change its default value.
DEPLOY_SAP = False

# flag to indicate if we use bidirectional forwarding rules in the automatic chaining process
BIDIRECTIONAL_CHAIN = False

class Gatekeeper(object):

    def __init__(self):
        self.services = dict()
        self.dcs = dict()
        self.net = None
        self.vnf_counter = 0  # used to generate short names for VNFs (Mininet limitation)
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
        self.package_content_path = os.path.join(CATALOG_FOLDER, "services/%s" % self.uuid)
        self.manifest = None
        self.nsd = None
        self.vnfds = dict()
        self.local_docker_files = dict()
        self.remote_docker_image_urls = dict()
        self.instances = dict()
        self.vnf_name2docker_name = dict()
        self.sap_identifiers = set()
        # lets generate a set of subnet configurations used for e-line chaining setup
        self.eline_subnets_src = generate_subnet_strings(50, start=200, subnet_size=24, ip=1)
        self.eline_subnets_dst = generate_subnet_strings(50, start=200, subnet_size=24, ip=2)

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

        # 2. Configure the chaining of the network functions (currently only E-Line and E-LAN links supported)
        vnf_id2vnf_name = defaultdict(lambda: "NotExistingNode",
                                      reduce(lambda x, y: dict(x, **y),
                                             map(lambda d: {d["vnf_id"]: d["vnf_name"]},
                                                 self.nsd["network_functions"])))

        # 3. compute placement of this service instance (adds DC names to VNFDs)
        if not GK_STANDALONE_MODE:
            #self._calculate_placement(FirstDcPlacement)
            self._calculate_placement(RoundRobinDcPlacement)
        # iterate over all vnfds that we have to start
        for vnfd in self.vnfds.itervalues():
            vnfi = None
            if not GK_STANDALONE_MODE:
                vnfi = self._start_vnfd(vnfd)
            self.instances[instance_uuid]["vnf_instances"].append(vnfi)

        if "virtual_links" in self.nsd:
            vlinks = self.nsd["virtual_links"]
            fwd_links = self.nsd["forwarding_graphs"][0]["constituent_virtual_links"]
            eline_fwd_links = [l for l in vlinks if (l["id"] in fwd_links) and (l["connectivity_type"] == "E-Line")]
            elan_fwd_links = [l for l in vlinks if (l["id"] in fwd_links) and (l["connectivity_type"] == "E-LAN")]

            GK.net.deployed_elines.extend(eline_fwd_links)
            GK.net.deployed_elans.extend(elan_fwd_links)

            # 4a. deploy E-Line links
            # cookie is used as identifier for the flowrules installed by the dummygatekeeper
            # eg. different services get a unique cookie for their flowrules
            cookie = 1
            for link in eline_fwd_links:
                src_id, src_if_name = link["connection_points_reference"][0].split(":")
                dst_id, dst_if_name = link["connection_points_reference"][1].split(":")

                # check if there is a SAP in the link
                if src_id in self.sap_identifiers:
                    src_docker_name = "{0}_{1}".format(src_id, src_if_name)
                    src_id = src_docker_name
                else:
                    src_docker_name = src_id

                if dst_id in self.sap_identifiers:
                    dst_docker_name = "{0}_{1}".format(dst_id, dst_if_name)
                    dst_id = dst_docker_name
                else:
                    dst_docker_name = dst_id

                src_name = vnf_id2vnf_name[src_id]
                dst_name = vnf_id2vnf_name[dst_id]

                LOG.debug(
                    "Setting up E-Line link. %s(%s:%s) -> %s(%s:%s)" % (
                        src_name, src_id, src_if_name, dst_name, dst_id, dst_if_name))

                if (src_name in self.vnfds) and (dst_name in self.vnfds):
                    network = self.vnfds[src_name].get("dc").net  # there should be a cleaner way to find the DCNetwork
                    LOG.debug(src_docker_name)
                    ret = network.setChain(
                        src_docker_name, dst_docker_name,
                        vnf_src_interface=src_if_name, vnf_dst_interface=dst_if_name,
                        bidirectional=BIDIRECTIONAL_CHAIN, cmd="add-flow", cookie=cookie, priority=10)

                    # re-configure the VNFs IP assignment and ensure that a new subnet is used for each E-Link
                    src_vnfi = self._get_vnf_instance(instance_uuid, src_name)
                    if src_vnfi is not None:
                        self._vnf_reconfigure_network(src_vnfi, src_if_name, self.eline_subnets_src.pop(0))
                    dst_vnfi = self._get_vnf_instance(instance_uuid, dst_name)
                    if dst_vnfi is not None:
                        self._vnf_reconfigure_network(dst_vnfi, dst_if_name, self.eline_subnets_dst.pop(0))

            # 4b. deploy E-LAN links
            base = 10
            for link in elan_fwd_links:

                elan_vnf_list=[]

                # generate lan ip address
                ip = 1
                for intf in link["connection_points_reference"]:
                    ip_address = generate_lan_string("10.0", base, subnet_size=24, ip=ip)
                    vnf_id, intf_name = intf.split(":")
                    if vnf_id in self.sap_identifiers:
                        src_docker_name = "{0}_{1}".format(vnf_id, intf_name)
                        vnf_id = src_docker_name
                    else:
                        src_docker_name = vnf_id
                    vnf_name = vnf_id2vnf_name[vnf_id]
                    LOG.debug(
                        "Setting up E-LAN link. %s(%s:%s) -> %s" % (
                            vnf_name, vnf_id, intf_name, ip_address))

                    if vnf_name in self.vnfds:
                        # re-configure the VNFs IP assignment and ensure that a new subnet is used for each E-LAN
                        # E-LAN relies on the learning switch capability of Ryu which has to be turned on in the topology
                        # (DCNetwork(controller=RemoteController, enable_learning=True)), so no explicit chaining is necessary.
                        vnfi = self._get_vnf_instance(instance_uuid, vnf_name)
                        if vnfi is not None:
                            self._vnf_reconfigure_network(vnfi, intf_name, ip_address)
                            # increase for the next ip address on this E-LAN
                            ip += 1

                            # add this vnf and interface to the E-LAN for tagging
                            network = self.vnfds[vnf_name].get("dc").net  # there should be a cleaner way to find the DCNetwork
                            elan_vnf_list.append({'name':src_docker_name,'interface':intf_name})


                # install the VLAN tags for this E-LAN
                network.setLAN(elan_vnf_list)
                # increase the base ip address for the next E-LAN
                base += 1

        # 5. run the emulator specific entrypoint scripts in the VNFIs of this service instance
        self._trigger_emulator_start_scripts_in_vnfis(self.instances[instance_uuid]["vnf_instances"])

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

        for v in vnf_instances:
            self._stop_vnfi(v)

        if not GK_STANDALONE_MODE:
            # remove placement?
            # self._remove_placement(RoundRobinPlacement)
            None

        # last step: remove the instance from the list of all instances
        del self.instances[instance_uuid]

    def _start_vnfd(self, vnfd):
        """
        Start a single VNFD of this service
        :param vnfd: vnfd descriptor dict
        :return:
        """
        # iterate over all deployment units within each VNFDs
        for u in vnfd.get("virtual_deployment_units"):
            # 1. get the name of the docker image to start and the assigned DC
            vnf_name = vnfd.get("name")
            if vnf_name not in self.remote_docker_image_urls:
                raise Exception("No image name for %r found. Abort." % vnf_name)
            docker_name = self.remote_docker_image_urls.get(vnf_name)
            target_dc = vnfd.get("dc")
            # 2. perform some checks to ensure we can start the container
            assert(docker_name is not None)
            assert(target_dc is not None)
            if not self._check_docker_image_exists(docker_name):
                raise Exception("Docker image %r not found. Abort." % docker_name)

            # 3. get the resource limits
            res_req = u.get("resource_requirements")
            cpu_list = res_req.get("cpu").get("cores")
            if not cpu_list or len(cpu_list)==0:
                cpu_list="1"
            cpu_bw = res_req.get("cpu").get("cpu_bw")
            if not cpu_bw:
                cpu_bw=1
            mem_num = str(res_req.get("memory").get("size"))
            if len(mem_num)==0:
                mem_num="2"
            mem_unit = str(res_req.get("memory").get("size_unit"))
            if str(mem_unit)==0:
                mem_unit="GB"
            mem_limit = float(mem_num)
            if mem_unit=="GB":
                mem_limit=mem_limit*1024*1024*1024
            elif mem_unit=="MB":
                mem_limit=mem_limit*1024*1024
            elif mem_unit=="KB":
                mem_limit=mem_limit*1024
            mem_lim = int(mem_limit)
            cpu_period, cpu_quota = self._calculate_cpu_cfs_values(float(cpu_bw))

            # 4. do the dc.startCompute(name="foobar") call to run the container
            # TODO consider flavors, and other annotations
            intfs = vnfd.get("connection_points")

            # TODO: get all vnf id's from the nsd for this vnfd and use those as dockername
            # use the vnf_id in the nsd as docker name
            # so deployed containers can be easily mapped back to the nsd
            vnf_name2id = defaultdict(lambda: "NotExistingNode",
                                          reduce(lambda x, y: dict(x, **y),
                                                 map(lambda d: {d["vnf_name"]: d["vnf_id"]},
                                                     self.nsd["network_functions"])))
            self.vnf_name2docker_name[vnf_name] = vnf_name2id[vnf_name]
            # self.vnf_name2docker_name[vnf_name] = GK.get_next_vnf_name()

            LOG.info("Starting %r as %r in DC %r" % (vnf_name, self.vnf_name2docker_name[vnf_name], vnfd.get("dc")))
            LOG.debug("Interfaces for %r: %r" % (vnf_name, intfs))
            vnfi = target_dc.startCompute(self.vnf_name2docker_name[vnf_name], network=intfs, image=docker_name, flavor_name="small",
                    cpu_quota=cpu_quota, cpu_period=cpu_period, cpuset=cpu_list, mem_limit=mem_lim)
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
        LOG.info("Stopping the vnf instance contained in %r in DC %r" % (status["name"], dc))
        dc.stopCompute(status["name"])

    def _get_vnf_instance(self, instance_uuid, name):
        """
        Returns the Docker object for the given VNF name (or Docker name).
        :param instance_uuid: UUID of the service instance to search in.
        :param name: VNF name or Docker name. We are fuzzy here.
        :return:
        """
        dn = name
        if name in self.vnf_name2docker_name:
            dn = self.vnf_name2docker_name[name]
        for vnfi in self.instances[instance_uuid]["vnf_instances"]:
            if vnfi.name == dn:
                return vnfi
        LOG.warning("No container with name: %r found.")
        return None

    @staticmethod
    def _vnf_reconfigure_network(vnfi, if_name, net_str):
        """
        Reconfigure the network configuration of a specific interface
        of a running container.
        :param vnfi: container instacne
        :param if_name: interface name
        :param net_str: network configuration string, e.g., 1.2.3.4/24
        :return:
        """
        intf = vnfi.intf(intf=if_name)
        if intf is not None:
            intf.setIP(net_str)
            LOG.debug("Reconfigured network of %s:%s to %r" % (vnfi.name, if_name, net_str))
        else:
            LOG.warning("Interface not found: %s:%s. Network reconfiguration skipped." % (vnfi.name, if_name))


    def _trigger_emulator_start_scripts_in_vnfis(self, vnfi_list):
        for vnfi in vnfi_list:
            config = vnfi.dcinfo.get("Config", dict())
            env = config.get("Env", list())
            for env_var in env:
                var, cmd = map(str.strip, map(str, env_var.split('=', 1)))
                LOG.debug("%r = %r" % (var , cmd))
                if var=="SON_EMU_CMD":
                    LOG.info("Executing entry point script in %r: %r" % (vnfi.name, cmd))
                    # execute command in new thread to ensure that GK is not blocked by VNF
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
            LOG.debug("Loaded NSD: %r" % self.nsd.get("name"))

    def _load_vnfd(self):
        """
        Load all VNFD YAML files referenced in MANIFEST.MF and keep them in dict.
        :return:
        """
        if "package_content" in self.manifest:
            for pc in self.manifest.get("package_content"):
                if pc.get("content-type") == "application/sonata.function_descriptor":
                    vnfd_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(pc.get("name")))
                    vnfd = load_yaml(vnfd_path)
                    self.vnfds[vnfd.get("name")] = vnfd
                    LOG.debug("Loaded VNFD: %r" % vnfd.get("name"))

    def _load_saps(self):
        # Each Service Access Point (connection_point) in the nsd is getting its own container
        SAPs = [p["id"] for p in self.nsd["connection_points"] if p["type"] == "interface"]
        for sap in SAPs:
            # endpoints needed in this service
            sap_vnf_id, sap_vnf_interface = sap.split(':')
            # set of the connection_point ids found in the nsd (in the examples this is 'ns')
            self.sap_identifiers.add(sap_vnf_id)

            sap_docker_name = "%s_%s" % (sap_vnf_id, sap_vnf_interface)

            # add SAP to self.vnfds
            sapfile = pkg_resources.resource_filename(__name__, "sap_vnfd.yml")
            sap_vnfd = load_yaml(sapfile)
            sap_vnfd["connection_points"][0]["id"] = sap_vnf_interface
            sap_vnfd["name"] = sap_docker_name
            self.vnfds[sap_docker_name] = sap_vnfd
            # add SAP vnf to list in the NSD so it is deployed later on
            # each SAP get a unique VNFD and vnf_id in the NSD
            self.nsd["network_functions"].append({"vnf_id": sap_docker_name, "vnf_name": sap_docker_name})
            LOG.debug("Loaded SAP: %r" % sap_vnfd.get("name"))

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
        for k, v in self.vnfds.iteritems():
            for vu in v.get("virtual_deployment_units"):
                if vu.get("vm_image_format") == "docker":
                    url = vu.get("vm_image")
                    if url is not None:
                        url = url.replace("http://", "")
                        self.remote_docker_image_urls[k] = url
                        LOG.debug("Found Docker image URL (%r): %r" % (k, self.remote_docker_image_urls[k]))

    def _build_images_from_dockerfiles(self):
        """
        Build Docker images for each local Dockerfile found in the package: self.local_docker_files
        """
        if GK_STANDALONE_MODE:
            return  # do not build anything in standalone mode
        dc = DockerClient()
        LOG.info("Building %d Docker images (this may take several minutes) ..." % len(self.local_docker_files))
        for k, v in self.local_docker_files.iteritems():
            for line in dc.build(path=v.replace("Dockerfile", ""), tag=k, rm=False, nocache=False):
                LOG.debug("DOCKER BUILD: %s" % line)
            LOG.info("Docker image created: %s" % k)

    def _pull_predefined_dockerimages(self):
        """
        If the package contains URLs to pre-build Docker images, we download them with this method.
        """
        dc = DockerClient()
        for url in self.remote_docker_image_urls.itervalues():
            if not FORCE_PULL:  # only pull if not present (speedup for development)
                if len(dc.images.list(name=url)) > 0:
                    LOG.debug("Image %r present. Skipping pull." % url)
                    continue
            LOG.info("Pulling image: %r" % url)
            # this seems to fail with latest docker api version 2.0.2
            # dc.images.pull(url,
            #        insecure_registry=True)
            #using docker cli instead
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
        p.place(self.nsd, self.vnfds, GK.dcs)
        LOG.info("Using placement algorithm: %r" % p.__class__.__name__)
        # lets print the placement result
        for name, vnfd in self.vnfds.iteritems():
            LOG.info("Placed VNF %r on DC %r" % (name, str(vnfd.get("dc"))))

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
        LOG.debug("cpu_period is %r, cpu_percentage is %r" % (cpu_period, cpu_time_percentage))
        cpu_quota = cpu_period * cpu_time_percentage  # calculate the fraction of cpu time for this container
        # ATTENTION >= 1000 to avoid a invalid argument system error ... no idea why
        if cpu_quota < 1000:
            LOG.debug("cpu_quota before correcting: %r" % cpu_quota)
            cpu_quota = 1000
            LOG.warning("Increased CPU quota to avoid system error.")
        LOG.debug("Calculated: cpu_period=%f / cpu_quota=%f" % (cpu_period, cpu_quota))
        return int(cpu_period), int(cpu_quota)


"""
Some (simple) placement algorithms
"""


class FirstDcPlacement(object):
    """
    Placement: Always use one and the same data center from the GK.dcs dict.
    """
    def place(self, nsd, vnfds, dcs):
        for name, vnfd in vnfds.iteritems():
            vnfd["dc"] = list(dcs.itervalues())[0]


class RoundRobinDcPlacement(object):
    """
    Placement: Distribute VNFs across all available DCs in a round robin fashion.
    """
    def place(self, nsd, vnfds, dcs):
        c = 0
        dcs_list = list(dcs.itervalues())
        for name, vnfd in vnfds.iteritems():
            vnfd["dc"] = dcs_list[c % len(dcs_list)]
            c += 1  # inc. c to use next DC




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
            print(request.files)
            # lets search for the package in the request
            if "package" in request.files:
                son_file = request.files["package"]
            # elif "file" in request.files:
            #     son_file = request.files["file"]
            else:
                return {"service_uuid": None, "size": 0, "sha1": None, "error": "upload failed. file not found."}, 500
            # generate a uuid to reference this package
            service_uuid = str(uuid.uuid4())
            file_hash = hashlib.sha1(str(son_file)).hexdigest()
            # ensure that upload folder exists
            ensure_dir(UPLOAD_FOLDER)
            upload_path = os.path.join(UPLOAD_FOLDER, "%s.son" % service_uuid)
            # store *.son file to disk
            son_file.save(upload_path)
            size = os.path.getsize(upload_path)
            # create a service object and register it
            s = Service(service_uuid, file_hash, upload_path)
            GK.register_service_package(service_uuid, s)
            # generate the JSON result
            return {"service_uuid": service_uuid, "size": size, "sha1": file_hash, "error": None}, 201
        except Exception as ex:
            LOG.exception("Service package upload failed:")
            return {"service_uuid": None, "size": 0, "sha1": None, "error": "upload failed"}, 500

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
        # try to extract the service uuid from the request
        json_data = request.get_json(force=True)
        service_uuid = json_data.get("service_uuid")

        # lets be a bit fuzzy here to make testing easier
        if service_uuid is None and len(GK.services) > 0:
            # if we don't get a service uuid, we simple start the first service in the list
            service_uuid = list(GK.services.iterkeys())[0]

        if service_uuid in GK.services:
            # ok, we have a service uuid, lets start the service
            service_instance_uuid = GK.services.get(service_uuid).start_service()
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
            #if we don't get a service uuid, we simply stop the last service in the list
            service_uuid = list(GK.services.iterkeys())[0]
        if instance_uuid is None and len(GK.services[service_uuid].instances) > 0:
            instance_uuid = list(GK.services[service_uuid].instances.iterkeys())[0]

        if service_uuid in GK.services and instance_uuid in GK.services[service_uuid].instances:
            # valid service and instance UUID, stop service
            GK.services.get(service_uuid).stop_service(instance_uuid)
            return "service instance with uuid %r stopped." % instance_uuid,200
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
api.add_resource(Packages, '/packages')
api.add_resource(Instantiations, '/instantiations')
api.add_resource(Exit, '/emulator/exit')


#def initialize_GK():
#    global GK
#    GK = Gatekeeper()


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
            LOG.exception("YAML parse error")
            r = dict()
    return r


def make_relative_path(path):
    if path.startswith("file://"):
        path = path.replace("file://", "", 1)
    if path.startswith("/"):
        path = path.replace("/", "", 1)
    return path


def generate_lan_string(prefix, base, subnet_size=24, ip=0):
    """
    Helper to generate different network configuration strings.
    """
    r = "%s.%d.%d/%d" % (prefix, base, ip, subnet_size)
    return r


def generate_subnet_strings(n, start=1, subnet_size=24, ip=0):
    """
    Helper to generate different network configuration strings.
    """
    r = list()
    for i in range(start, start + n):
        r.append("%d.0.0.%d/%d" % (i, ip, subnet_size))
    return r

def get_dc_network():
    """
    retrieve the DCnetwork where this dummygatekeeper (GK) connects to.
    Assume at least 1 datacenter is connected to this GK, and that all datacenters belong to the same DCNetwork
    :return:
    """
    assert (len(GK.dcs) > 0)
    return GK.dcs.values()[0].net

if __name__ == '__main__':
    """
    Lets allow to run the API in standalone mode.
    """
    GK_STANDALONE_MODE = True
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    start_rest_api("0.0.0.0", 8000)

