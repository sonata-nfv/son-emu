"""
This module implements a simple REST API that behaves like SONATA's gatekeeper.

It is only used to support the development of SONATA's SDK tools and to demonstrate
the year 1 version of the emulator until the integration with WP4's orchestrator is done.
"""

import logging
import os
import uuid
import hashlib
import json
from flask import Flask, request
import flask_restful as fr

logging.getLogger("werkzeug").setLevel(logging.WARNING)


UPLOAD_FOLDER = "/tmp/son-dummy-gk/uploads/"
CATALOG_FOLDER = "/tmp/son-dummy-gk/catalog/"


class Gatekeeper(object):

    def __init__(self):
        self.packages = dict()
        self.instantiations = dict()
        logging.info("Create SONATA dummy gatekeeper.")

    def unpack_service_package(self, service_uuid):
        # TODO implement method
        # 1. unzip *.son file and store contents in CATALOG_FOLDER/services/<service_uuid>/
        pass

    def start_service(self, service_uuid):
        # TODO implement method
        # 1. parse descriptors
        # 2. do the corresponding dc.startCompute(name="foobar") calls
        # 3. store references to the compute objects in self.instantiations
        pass


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
            file = request.files['file']
            # generate a uuid to reference this package
            service_uuid = str(uuid.uuid4())
            hash = hashlib.sha1(str(file)).hexdigest()
            # ensure that upload folder exists
            ensure_dir(UPLOAD_FOLDER)
            upload_path = os.path.join(UPLOAD_FOLDER, "%s.son" % service_uuid)
            # store *.son file to disk
            file.save(upload_path)
            size = os.path.getsize(upload_path)
            # store a reference to the uploaded package in our gatekeeper
            GK.packages[service_uuid] = upload_path
            # generate the JSON result
            return {"service_uuid": service_uuid, "size": size, "sha1": hash, "error": None}
        except Exception as ex:
            logging.exception("Service package upload failed:")
            return {"service_uuid": None, "size": 0, "sha1": None, "error": "upload failed"}

    def get(self):
        """
        Return a list of UUID's of uploaded service packages.
        :return: dict/list
        """
        return {"service_uuid_list": list(GK.packages.iterkeys())}


class Instantiations(fr.Resource):

    def post(self):
        """
        Instantiate a service specified by its UUID.
        Will return a new UUID to identify the running service instance.
        :return: UUID
        """
        # TODO implement method (start real service)
        json_data = request.get_json(force=True)
        service_uuid = json_data.get("service_uuid")
        if service_uuid is not None:
            service_instance_uuid = str(uuid.uuid4())
            GK.instantiations[service_instance_uuid] = service_uuid
            logging.info("Starting service %r" % service_uuid)
            return {"service_instance_uuid": service_instance_uuid}
        return None

    def get(self):
        """
        Returns a list of UUIDs containing all running services.
        :return: dict / list
        """
        # TODO implement method
        return {"service_instance_uuid_list": list(GK.instantiations.iterkeys())}

# create a single, global GK object
GK = Gatekeeper()
# setup Flask
app = Flask(__name__)
app.config['MAX_CONTENT_LENGTH'] = 512 * 1024 * 1024  # 512 MB max upload
api = fr.Api(app)
# define endpoints
api.add_resource(Packages, '/api/packages/uploads')
api.add_resource(Instantiations, '/api/instantiations')


def start_rest_api(host, port):
    # start the Flask server (not the best performance but ok for our use case)
    app.run(host=host,
            port=port,
            debug=True,
            use_reloader=False  # this is needed to run Flask in a non-main thread
            )


def ensure_dir(name):
    if not os.path.exists(name):
       os.makedirs(name)


if __name__ == '__main__':
    """
    Lets allow to run the API in standalone mode.
    """
    logging.getLogger("werkzeug").setLevel(logging.INFO)
    start_rest_api("0.0.0.0", 8000)

