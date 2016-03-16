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
from docker import Client as DockerClient
from flask import Flask, request
import flask_restful as fr

LOG = logging.getLogger("sonata-dummy-gatekeeper")
LOG.setLevel(logging.DEBUG)
logging.getLogger("werkzeug").setLevel(logging.WARNING)


UPLOAD_FOLDER = "/tmp/son-dummy-gk/uploads/"
CATALOG_FOLDER = "/tmp/son-dummy-gk/catalog/"


class Gatekeeper(object):

    def __init__(self):
        self.services = dict()
        self.dcs = dict()
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
        return "sonvnf%d" % self.vnf_counter


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
        self.instances = dict()

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
        self._load_docker_files()
        # 3. prepare container images (e.g. download or build Dockerfile)
        self._build_images_from_dockerfiles()
        self._download_predefined_dockerimages()

        LOG.info("On-boarded service: %r" % self.manifest.get("package_name"))

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
        # 2. compute placement of this service instance (adds DC names to VNFDs)
        self._calculate_placement(FirstDcPlacement)
        # iterate over all vnfds that we have to start
        for vnfd in self.vnfds.itervalues():
            # iterate over all deployment units within each VNFDs
            for u in vnfd.get("virtual_deployment_units"):
                # 3. get the name of the docker image to start and the assigned DC
                docker_name = u.get("vm_image")
                target_dc = vnfd.get("dc")
                # 4. perform some checks to ensure we can start the container
                assert(docker_name is not None)
                assert(target_dc is not None)
                if not self._check_docker_image_exists(docker_name):
                    raise Exception("Docker image %r not found. Abort." % docker_name)
                # 5. do the dc.startCompute(name="foobar") call to run the container
                # TODO consider flavors, and other annotations
                vnfi = target_dc.startCompute(GK.get_next_vnf_name(), image=docker_name, flavor_name="small")
                # 6. store references to the compute objects in self.instances
                self.instances[instance_uuid]["vnf_instances"].append(vnfi)
        LOG.info("Service started. Instance id: %r" % instance_uuid)
        return instance_uuid

    def _unpack_service_package(self):
        """
        unzip *.son file and store contents in CATALOG_FOLDER/services/<service_uuid>/
        """
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
            LOG.debug("Loaded NSD: %r" % self.nsd.get("ns_name"))

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
                    self.vnfds[vnfd.get("vnf_name")] = vnfd
                    LOG.debug("Loaded VNFD: %r" % vnfd.get("vnf_name"))

    def _load_docker_files(self):
        """
        Get all paths to Dockerfiles from MANIFEST.MF and store them in dict.
        :return:
        """
        if "package_content" in self.manifest:
            for df in self.manifest.get("package_content"):
                if df.get("content-type") == "application/sonata.docker_files":
                    docker_path = os.path.join(
                        self.package_content_path,
                        make_relative_path(df.get("name")))
                    # FIXME: Mapping to docker image names is hardcoded because of the missing mapping in the example package
                    self.local_docker_files[helper_map_docker_name(df.get("name"))] = docker_path
                    LOG.debug("Found Dockerfile: %r" % docker_path)

    def _build_images_from_dockerfiles(self):
        """
        Build Docker images for each local Dockerfile found in the package: self.local_docker_files
        """
        dc = DockerClient()
        LOG.info("Building %d Docker images (this may take several minutes) ..." % len(self.local_docker_files))
        for k, v in self.local_docker_files.iteritems():
            for line in dc.build(path=v.replace("Dockerfile", ""), tag=k, rm=False, nocache=False):
                LOG.debug("DOCKER BUILD: %s" % line)
            LOG.info("Docker image created: %s" % k)

    def _download_predefined_dockerimages(self):
        """
        If the package contains URLs to pre-build Docker images, we download them with this method.
        """
        # TODO implement this if we want to be able to download docker images instead of building them
        pass

    def _check_docker_image_exists(self, image_name):
        """
        Query the docker service and check if the given image exists
        :param image_name: name of the docker image
        :return:
        """
        return len(DockerClient().images(image_name)) > 0

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
            son_file = request.files['file']
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
            return {"service_uuid": service_uuid, "size": size, "sha1": file_hash, "error": None}
        except Exception as ex:
            LOG.exception("Service package upload failed:")
            return {"service_uuid": None, "size": 0, "sha1": None, "error": "upload failed"}

    def get(self):
        """
        Return a list of UUID's of uploaded service packages.
        :return: dict/list
        """
        return {"service_uuid_list": list(GK.services.iterkeys())}


class Instantiations(fr.Resource):

    def post(self):
        """
        Instantiate a service specified by its UUID.
        Will return a new UUID to identify the running service instance.
        :return: UUID
        """
        json_data = request.get_json(force=True)
        service_uuid = list(GK.services.iterkeys())[0] #json_data.get("service_uuid") # TODO only for quick testing
        if service_uuid in GK.services:
            service_instance_uuid = GK.services.get(service_uuid).start_service()
            return {"service_instance_uuid": service_instance_uuid}
        return "Service not found", 404

    def get(self):
        """
        Returns a list of UUIDs containing all running services.
        :return: dict / list
        """
        # TODO implement method
        return {"service_instance_uuid_list": list()}


# create a single, global GK object
GK = Gatekeeper()
# setup Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload
api = fr.Api(app)
# define endpoints
api.add_resource(Packages, '/api/packages')
api.add_resource(Instantiations, '/api/instantiations')


def start_rest_api(host, port, datacenters=dict()):
    GK.dcs = datacenters
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
    if path.startswith("/"):
        return path.replace("/", "", 1)
    return path


def helper_map_docker_name(name):
    """
    Quick hack to fix missing dependency in example package.
    """
    # FIXME remove this when package description is fixed
    mapping = {
        "/docker_files/iperf/Dockerfile": "iperf_docker",
        "/docker_files/firewall/Dockerfile": "fw_docker",
        "/docker_files/tcpdump/Dockerfile": "tcpdump_docker"
    }
    return mapping.get(name)


if __name__ == '__main__':
    """
    Lets allow to run the API in standalone mode.
    """
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    start_rest_api("0.0.0.0", 8000)

