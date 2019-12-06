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
from flask_restful import Resource
from flask import Response, request
from emuvim.api.openstack.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from emuvim.api.openstack.helper import get_host
import logging
import json
import uuid
from mininet.link import Link


LOG = logging.getLogger("api.openstack.nova")


class NovaDummyApi(BaseOpenstackDummy):
    def __init__(self, in_ip, in_port, compute):
        super(NovaDummyApi, self).__init__(in_ip, in_port)
        self.compute = compute
        self.compute.add_flavor('m1.tiny', 1, 512, "MB", 1, "GB")
        self.compute.add_flavor('m1.nano', 1, 64, "MB", 0, "GB")
        self.compute.add_flavor('m1.micro', 1, 128, "MB", 0, "GB")
        self.compute.add_flavor('m1.small', 1, 1024, "MB", 2, "GB")

        self.api.add_resource(NovaVersionsList, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaVersionShow, "/v2.1/<id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersApi, "/v2.1/<id>/servers",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersAndPortsApi, "/v2.1/<id>/servers/andPorts",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListServersDetailed, "/v2.1/<id>/servers/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaShowServerDetails, "/v2.1/<id>/servers/<serverid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaInterfaceToServer, "/v2.1/<id>/servers/<serverid>/os-interface",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaShowAndDeleteInterfaceAtServer, "/v2.1/<id>/servers/<serverid>/os-interface/<port_id>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavors, "/v2.1/<id>/flavors", "/v2/<id>/flavors",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavorsDetails, "/v2.1/<id>/flavors/detail", "/v2/<id>/flavors/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListFlavorById, "/v2.1/<id>/flavors/<flavorid>", "/v2/<id>/flavors/<flavorid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImages, "/v2.1/<id>/images",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImagesDetails, "/v2.1/<id>/images/detail",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaListImageById, "/v2.1/<id>/images/<imageid>",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(NovaLimits, "/v2.1/<id>/limits",
                              resource_class_kwargs={'api': self})


class NovaVersionsList(Resource):
    def __init__(self, api):
        self.api = api

    def get(self):
        """
        Lists API versions.

        :return: Returns a json with API versions.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = """
                {
                    "versions": [
                        {
                            "id": "v2.1",
                            "links": [
                                {
                                    "href": "http://%s:%d/v2.1/",
                                    "rel": "self"
                                }
                            ],
                            "status": "CURRENT",
                            "version": "2.38",
                            "min_version": "2.1",
                            "updated": "2013-07-23T11:33:21Z"
                        }
                    ]
                }
            """ % (get_host(request), self.api.port)

            response = Response(resp, status=200, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(u"%s: Could not show list of versions." % __name__)
            return str(ex), 500


class NovaVersionShow(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Returns API details.

        :param id:
        :type id: ``str``
        :return: Returns a json with API details.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            resp = """
            {
                "version": {
                    "id": "v2.1",
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/",
                            "rel": "self"
                        },
                        {
                            "href": "http://docs.openstack.org/",
                            "rel": "describedby",
                            "type": "text/html"
                        }
                    ],
                    "media-types": [
                        {
                            "base": "application/json",
                            "type": "application/vnd.openstack.compute+json;version=2.1"
                        }
                    ],
                    "status": "CURRENT",
                    "version": "2.38",
                    "min_version": "2.1",
                    "updated": "2013-07-23T11:33:21Z"
                }
            }
            """ % (get_host(request), self.api.port)

            response = Response(resp, status=200, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(u"%s: Could not show list of versions." % __name__)
            return str(ex), 500


class NovaListServersApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Creates a list with all running servers and their detailed information.

        :param id: Used to create a individual link to quarry further information.
        :type id: ``str``
        :return: Returns a json response with a dictionary that contains the server information.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            resp = dict()
            resp['servers'] = list()
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (get_host(request),
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]

                resp['servers'].append(s)

            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of servers." % __name__)
            return str(ex), 500

    def post(self, id):
        """
        Creates a server instance.

        :param id: tenant id, we ignore this most of the time
        :type id: ``str``
        :return: Returns a flask response, with detailed information about the just created server.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            server_dict = json.loads(request.data)['server']
            networks = server_dict.get('networks', None)
            name = str(self.api.compute.dc.label) + "_" + server_dict["name"]

            if self.api.compute.find_server_by_name_or_id(name) is not None:
                LOG.error("Server with name %s already exists. 409" % name)
                return Response(
                    "Server with name %s already exists." % name, status=409)
            # TODO: not finished!
            server = self.api.compute.create_server(name)
            server.full_name = str(
                self.api.compute.dc.label) + "_" + server_dict["name"]
            server.template_name = server_dict["name"]
            if "metadata" in server_dict:
                server.properties = server_dict["metadata"]

            for flavor in self.api.compute.flavors.values():
                if flavor.id == server_dict.get('flavorRef', ''):
                    server.flavor = flavor.name
            for image in self.api.compute.images.values():
                if image.id in server_dict['imageRef']:
                    server.image = image.name

            if networks is not None:
                for net in networks:
                    port_name_or_id = net.get('port', "")
                    port = self.api.compute.find_port_by_name_or_id(port_name_or_id)
                    if port is not None:
                        server.port_names.append(port_name_or_id)
                    else:
                        return Response(
                            "Currently only networking by port is supported.", status=400)

            self.api.compute._start_compute(server)

            response = NovaShowServerDetails(self.api).get(id, server.id)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(u"%s: Could not create the server." % __name__)
            return str(ex), 500


class NovaListServersAndPortsApi(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Creates a list with all running servers and their detailed information. This function also presents all
        port information of each server.

        :param id: Used to create a individual link to quarry further information.
        :type id: ``str``
        :return: Returns a json response with a dictionary that contains the server information.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            resp = dict()
            resp['servers'] = list()
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (get_host(request),
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]

                s['ports'] = list()
                for port_name in server.port_names:
                    port = self.api.compute.find_port_by_name_or_id(port_name)
                    if port is None:
                        continue

                    tmp = port.create_port_dict(self.api.compute)
                    tmp['intf_name'] = port.intf_name
                    s['ports'].append(tmp)

                resp['servers'].append(s)

            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of servers." % __name__)
            return str(ex), 500


class NovaListServersDetailed(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        As List Servers, it lists all running servers and their details but furthermore it also states the
        used flavor and the server image.

        :param id: tenant id, used for the 'href' link.
        :type id: ``str``
        :return: Returns a flask response, with detailed information aboit the servers and their flavor and image.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))

        try:
            resp = {"servers": list()}
            for server in self.api.compute.computeUnits.values():
                s = server.create_server_dict(self.api.compute)
                s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (get_host(request),
                                                                            self.api.port,
                                                                            id,
                                                                            server.id)}]
                flavor = self.api.compute.flavors[server.flavor]
                s['flavor'] = {
                    "id": flavor.id,
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                         self.api.port,
                                                                         id,
                                                                         flavor.id),
                            "rel": "bookmark"
                        }
                    ]
                }
                image = self.api.compute.images[server.image]
                s['image'] = {
                    "id": image.id,
                    "links": [
                        {
                            "href": "http://%s:%d/v2.1/%s/images/%s" % (get_host(request),
                                                                        self.api.port,
                                                                        id,
                                                                        image.id),
                            "rel": "bookmark"
                        }
                    ]
                }

                resp['servers'].append(s)

            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of servers." % __name__)
            return str(ex), 500


class NovaListFlavors(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Lists all available flavors.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :return: Returns a flask response with a list of all flavors.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in self.api.compute.flavors.values():
                f = flavor.__dict__.copy()
                f['id'] = flavor.id
                f['name'] = flavor.name
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                            self.api.port,
                                                                            id,
                                                                            flavor.id)}]
                resp['flavors'].append(f)

            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of servers." % __name__)
            return str(ex), 500

    def post(self, id):
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        data = json.loads(request.data).get("flavor")
        LOG.warning("Create Flavor: %s" % str(data))
        # add to internal dict
        f = self.api.compute.add_flavor(
            data.get("name"),
            data.get("vcpus"),
            data.get("ram"), "MB",
            data.get("disk"), "GB")
        # create response based on incoming data
        data["id"] = f.id
        data["links"] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                       self.api.port,
                                                                       id,
                                                                       f.id)}]
        resp = {"flavor": data}
        return Response(json.dumps(resp), status=200,
                        mimetype="application/json")


class NovaListFlavorsDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Lists all flavors with additional information like ram and disk space.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :return: Returns a flask response with a list of all flavors with additional information.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['flavors'] = list()
            for flavor in self.api.compute.flavors.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = flavor.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                            self.api.port,
                                                                            id,
                                                                            flavor.id)}]
                f['OS-FLV-DISABLED:disabled'] = False
                f['OS-FLV-EXT-DATA:ephemeral'] = 0
                f['os-flavor-access:is_public'] = True
                f['ram'] = flavor.memory
                f['vcpus'] = flavor.cpu
                f['swap'] = 0
                f['disk'] = flavor.storage
                f['rxtx_factor'] = 1.0
                resp['flavors'].append(f)

            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of servers." % __name__)
            return str(ex), 500

    def post(self, id):
        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        data = json.loads(request.data).get("flavor")
        LOG.warning("Create Flavor: %s" % str(data))
        # add to internal dict
        f = self.api.compute.add_flavor(
            data.get("name"),
            data.get("vcpus"),
            data.get("ram"), "MB",
            data.get("disk"), "GB")
        # create response based on incoming data
        data["id"] = f.id
        data["links"] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                       self.api.port,
                                                                       id,
                                                                       f.id)}]
        resp = {"flavor": data}
        return Response(json.dumps(resp), status=200,
                        mimetype="application/json")


class NovaListFlavorById(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, flavorid):
        """
        Returns details about one flavor.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :param flavorid: Represents the flavor.
        :type flavorid: ``str``
        :return: Returns a flask response with detailed information about the flavor.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['flavor'] = dict()
            flavor = self.api.compute.flavors.get(flavorid, None)
            if flavor is None:
                for f in self.api.compute.flavors.values():
                    if f.id == flavorid:
                        flavor = f
                        break
            resp['flavor']['id'] = flavor.id
            resp['flavor']['name'] = flavor.name
            resp['flavor']['links'] = [{'href': "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                                     self.api.port,
                                                                                     id,
                                                                                     flavor.id)}]
            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(u"%s: Could not retrieve flavor with id %s" %
                          (__name__, flavorid))
            return str(ex), 500

    def delete(self, id, flavorid):
        """
        Removes the given flavor.
        Does not really remove anything from the machine, just fakes an OK.
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return Response("", status=204, mimetype="application/json")


class NovaListImages(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Creates a list of all usable images.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :return: Returns a flask response with a list of available images.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['images'] = list()
            for image in self.api.compute.images.values():
                f = dict()
                f['id'] = image.id
                f['name'] = str(image.name).replace(":latest", "")
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (get_host(request),
                                                                           self.api.port,
                                                                           id,
                                                                           image.id)}]
                resp['images'].append(f)
            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of images." % __name__)
            return str(ex), 500


class NovaListImagesDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        As List Images but with additional metadata.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :return: Returns a flask response with a list of images and their metadata.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            resp['images'] = list()
            for image in self.api.compute.images.values():
                # use the class dict. it should work fine
                # but use a copy so we don't modifiy the original
                f = image.__dict__.copy()
                # add additional expected stuff stay openstack compatible
                f['name'] = str(image.name).replace(":latest", "")
                f['links'] = [{'href': "http://%s:%d/v2.1/%s/images/%s" % (get_host(request),
                                                                           self.api.port,
                                                                           id,
                                                                           image.id)}]
                f['metadata'] = {
                    "architecture": "x86_64",
                    "auto_disk_config": "True",
                    "kernel_id": "nokernel",
                    "ramdisk_id": "nokernel"
                }
                resp['images'].append(f)

            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of images." % __name__)
            return str(ex), 500


class NovaListImageById(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, imageid):
        """
        Gets an image by id from the emulator with openstack nova compliant return values.

        :param id: tenantid, we ignore this most of the time
        :type id: ``str``
        :param imageid: id of the image. If it is 1 the dummy CREATE-IMAGE is returned
        :type imageid: ``str``
        :return: Returns a flask response with the information about one image.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = dict()
            i = resp['image'] = dict()
            for image in self.api.compute.images.values():
                if image.id == imageid or image.name == imageid:
                    i['id'] = image.id
                    i['name'] = image.name

                    return Response(json.dumps(resp), status=200,
                                    mimetype="application/json")

            response = Response(
                "Image with id or name %s does not exists." % imageid, status=404)
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(u"%s: Could not retrieve image with id %s." %
                          (__name__, imageid))
            return str(ex), 500

    def delete(self, id, imageid):
        """
        Removes the given image.
        Does not really remove anything from the machine, just fakes an OK.
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        return Response("", status=204, mimetype="application/json")


class NovaShowServerDetails(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id, serverid):
        """
        Returns detailed information about the specified server.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :param serverid: Specifies the requested server.
        :type serverid: ``str``
        :return: Returns a flask response with details about the server.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response(
                    "Server with id or name %s does not exists." % serverid, status=404)
            s = server.create_server_dict()
            s['links'] = [{'href': "http://%s:%d/v2.1/%s/servers/%s" % (get_host(request),
                                                                        self.api.port,
                                                                        id,
                                                                        server.id)}]

            flavor = self.api.compute.flavors[server.flavor]
            s['flavor'] = {
                "id": flavor.id,
                "links": [
                    {
                        "href": "http://%s:%d/v2.1/%s/flavors/%s" % (get_host(request),
                                                                     self.api.port,
                                                                     id,
                                                                     flavor.id),
                        "rel": "bookmark"
                    }
                ]
            }
            image = self.api.compute.images[server.image]
            s['image'] = {
                "id": image.id,
                "links": [
                    {
                        "href": "http://%s:%d/v2.1/%s/images/%s" % (get_host(request),
                                                                    self.api.port,
                                                                    id,
                                                                    image.id),
                        "rel": "bookmark"
                    }
                ]
            }

            response = Response(json.dumps(
                {'server': s}), status=200, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the server details." % __name__)
            return str(ex), 500

    def delete(self, id, serverid):
        """
        Delete a server instance.

        :param id: tenant id, we ignore this most of the time
        :type id: ``str``
        :param serverid: The UUID of the server
        :type serverid: ``str``
        :return: Returns 204 if everything is fine.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s DELETE" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response('Could not find server.',
                                status=404, mimetype="application/json")

            self.api.compute.stop_compute(server)

            response = Response('', status=204, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(u"%s: Could not create the server." % __name__)
            return str(ex), 500


class NovaInterfaceToServer(Resource):
    def __init__(self, api):
        self.api = api

    def post(self, id, serverid):
        """
        Add an interface to the specified server.

        :param id: tenant id, we ignore this most of the time
        :type id: ``str``
        :param serverid: Specifies the server.
        :type serverid: ``str``
        :return: Returns a flask response with information about the attached interface.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response(
                    "Server with id or name %s does not exists." % serverid, status=404)

            if server.emulator_compute is None:
                LOG.error("The targeted container does not exist.")
                return Response(
                    "The targeted container of %s does not exist." % serverid, status=404)
            data = json.loads(request.data).get("interfaceAttachment")
            resp = dict()
            port = data.get("port_id", None)
            net = data.get("net_id", None)
            dc = self.api.compute.dc
            network_dict = dict()
            network = None

            if net is not None and port is not None:
                port = self.api.compute.find_port_by_name_or_id(port)
                network = self.api.compute.find_network_by_name_or_id(net)
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network_dict[network_dict['id']] = network.name
            elif net is not None:
                network = self.api.compute.find_network_by_name_or_id(net)
                if network is None:
                    return Response(
                        "Network with id or name %s does not exists." % net, status=404)
                port = self.api.compute.create_port("port:cp%s:fl:%s" %
                                                    (len(self.api.compute.ports), str(uuid.uuid4())))

                port.net_name = network.name
                port.ip_address = network.get_new_ip_address(port.name)
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network_dict[network_dict['id']] = network.name
            elif port is not None:
                port = self.api.compute.find_port_by_name_or_id(port)
                network_dict['id'] = port.intf_name
                network_dict['ip'] = port.ip_address
                network = self.api.compute.find_network_by_name_or_id(
                    port.net_name)
                network_dict[network_dict['id']] = network.name
            else:
                raise Exception(
                    "You can only attach interfaces by port or network at the moment")

            if network == self.api.manage.floating_network:
                dc.net.addLink(server.emulator_compute, self.api.manage.floating_switch,
                               params1=network_dict, cls=Link, intfName1=port.intf_name)
            else:
                dc.net.addLink(server.emulator_compute, dc.switch,
                               params1=network_dict, cls=Link, intfName1=port.intf_name)
            resp["port_state"] = "ACTIVE"
            resp["port_id"] = port.id
            resp["net_id"] = self.api.compute.find_network_by_name_or_id(
                port.net_name).id
            resp["mac_addr"] = port.mac_address
            resp["fixed_ips"] = list()
            fixed_ips = dict()
            fixed_ips["ip_address"] = port.ip_address
            fixed_ips["subnet_id"] = network.subnet_name
            resp["fixed_ips"].append(fixed_ips)
            response = Response(json.dumps(
                {"interfaceAttachment": resp}), status=202, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not add interface to the server." % __name__)
            return str(ex), 500


class NovaShowAndDeleteInterfaceAtServer(Resource):
    def __init__(self, api):
        self.api = api

    def delete(self, id, serverid, port_id):
        """
        Deletes an existing interface.

        :param id: tenant id, we ignore this most of the time
        :type id: ``str``
        :param serverid: Specifies the server, where the interface will be deleted.
        :type serverid: ``str``
        :param port_id: Specifies the port of the interface.
        :type port_id: ``str``
        :return: Returns a flask response with 202 if everything worked out. Otherwise it will return 404 and an
         error message.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            server = self.api.compute.find_server_by_name_or_id(serverid)
            if server is None:
                return Response(
                    "Server with id or name %s does not exists." % serverid, status=404)
            port = self.api.compute.find_port_by_name_or_id(port_id)
            if port is None:
                return Response(
                    "Port with id or name %s does not exists." % port_id, status=404)

            for link in self.api.compute.dc.net.links:
                if str(link.intf1) == port.intf_name and \
                        str(link.intf1.ip) == port.ip_address.split('/')[0]:
                    self.api.compute.dc.net.removeLink(link)
                    break

            response = Response("", status=202, mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not detach interface from the server." % __name__)
            return str(ex), 500


class NovaLimits(Resource):
    def __init__(self, api):
        self.api = api

    def get(self, id):
        """
        Returns the resource limits of the emulated cloud.
        https://developer.openstack.org/api-ref/compute/?expanded=show-rate-and-absolute-limits-detail#limits-limits

        TODO: For now we only return fixed limits, not based on the real deployment.

        :param id: tenant id, used for the 'href' link
        :type id: ``str``
        :return: Returns the resource limits.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        try:
            resp = {
                "limits": {
                    "absolute": {
                        "maxImageMeta": 12800,
                        "maxPersonality": 500,
                        "maxPersonalitySize": 1024000,
                        "maxSecurityGroupRules": 2000,
                        "maxSecurityGroups": 1000,
                        "maxServerMeta": 12800,
                        "maxTotalCores": 2000,
                        "maxTotalFloatingIps": 1000,
                        "maxTotalInstances": 1000,
                        "maxTotalKeypairs": 1000,
                        "maxTotalRAMSize": 5120000,
                        "maxServerGroups": 1000,
                        "maxServerGroupMembers": 1000,
                        "totalCoresUsed": 0,
                        "totalInstancesUsed": 0,
                        "totalRAMUsed": 0,
                        "totalSecurityGroupsUsed": 0,
                        "totalFloatingIpsUsed": 0,
                        "totalServerGroupsUsed": 0
                    },
                    "rate": []
                }
            }
            response = Response(json.dumps(resp), status=200,
                                mimetype="application/json")
            response.headers['Access-Control-Allow-Origin'] = '*'
            return response

        except Exception as ex:
            LOG.exception(
                u"%s: Could not retrieve the list of images." % __name__)
            return str(ex), 500
