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
from flask import request, Response
from emuvim.api.openstack.openstack_dummies.base_openstack_dummy import BaseOpenstackDummy
from emuvim.api.openstack.helper import get_host
import logging
import json

LOG = logging.getLogger("api.openstack.keystone")


class KeystoneDummyApi(BaseOpenstackDummy):
    def __init__(self, in_ip, in_port):
        super(KeystoneDummyApi, self).__init__(in_ip, in_port)

        self.api.add_resource(KeystoneListVersions, "/",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(KeystoneShowAPIv2, "/v2.0",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(KeystoneGetToken, "/v2.0/tokens",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(KeystoneShowAPIv3, "/v3.0",
                              resource_class_kwargs={'api': self})
        self.api.add_resource(
            KeystoneGetTokenv3, "/v3.0/auth/tokens", resource_class_kwargs={'api': self})


class KeystoneListVersions(Resource):
    """
    List all known keystone versions.
    Hardcoded for our version!
    """

    def __init__(self, api):
        self.api = api

    def get(self):
        """
        List API versions.

        :return: Returns the api versions.
        :rtype: :class:`flask.response` containing a static json encoded dict.
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))
        resp = dict()
        resp['versions'] = dict()

        version = [{
            "id": "v2.0",
            "links": [
                {
                    "href": "http://%s:%d/v2.0" % (get_host(request), self.api.port),
                    "rel": "self"
                }
            ],
            "media-types": [
                {
                    "base": "application/json",
                    "type": "application/vnd.openstack.identity-v2.0+json"
                }
            ],
            "status": "stable",
            "updated": "2014-04-17T00:00:00Z"
        }]
        resp['versions']['values'] = version

        return Response(json.dumps(resp), status=200,
                        mimetype='application/json')


class KeystoneShowAPIv2(Resource):
    """
    Entrypoint for all openstack clients.
    This returns all current entrypoints running on son-emu.
    """

    def __init__(self, api):
        self.api = api

    def get(self):
        """
        List API entrypoints.

        :return: Returns an openstack style response for all entrypoints.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))

        # neutron_port = self.api.port + 4696
        # heat_port = self.api.port + 3004

        resp = dict()
        resp['version'] = {
            "status": "stable",
            "media-types": [
                {
                    "base": "application/json",
                    "type": "application/vnd.openstack.identity-v2.0+json"
                }
            ],
            "id": "v2.0",
            "links": [
                {
                    "href": "http://%s:%d/v2.0" % (get_host(request), self.api.port),
                    "rel": "self"
                }
            ]
        }
        LOG.debug(json.dumps(resp))
        return Response(json.dumps(resp), status=200,
                        mimetype='application/json')


class KeystoneShowAPIv3(Resource):
    """
    Entrypoint for all openstack clients.
    This returns all current entrypoints running on son-emu.
    """

    def __init__(self, api):
        self.api = api

    def get(self):
        """
        List API entrypoints.

        :return: Returns an openstack style response for all entrypoints.
        :rtype: :class:`flask.response`
        """
        LOG.debug("API CALL: %s GET" % str(self.__class__.__name__))

        # neutron_port = self.api.port + 4696
        # heat_port = self.api.port + 3004

        resp = dict()
        resp['version'] = {
            "status": "stable",
            "media-types": [
                {
                    "base": "application/json",
                    "type": "application/vnd.openstack.identity-v3.0+json"
                }
            ],
            "id": "v3.0",
            "links": [
                {
                    "href": "http://%s:%d/v3.0" % (get_host(request), self.api.port),
                    "rel": "self"
                }
            ]
        }

        return Response(json.dumps(resp), status=200,
                        mimetype='application/json')


class KeystoneGetToken(Resource):
    """
    Returns a static keystone token.
    We don't do any validation so we don't care.
    """

    def __init__(self, api):
        self.api = api

    def post(self):
        """
        List API entrypoints.

        This is hardcoded. For a working "authentication" use these ENVVARS:

        * OS_AUTH_URL=http://<ip>:<port>/v2.0
        * OS_IDENTITY_API_VERSION=2.0
        * OS_TENANT_ID=fc394f2ab2df4114bde39905f800dc57
        * OS_REGION_NAME=RegionOne
        * OS_USERNAME=bla
        * OS_PASSWORD=bla

        :return: Returns an openstack style response for all entrypoints.
        :rtype: :class:`flask.response`
        """

        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            ret = dict()
            req = json.loads(request.data)
            ret['access'] = dict()
            ret['access']['token'] = dict()
            token = ret['access']['token']

            token['issued_at'] = "2014-01-30T15:30:58.819Z"
            token['expires'] = "2999-01-30T15:30:58.819Z"
            token['id'] = req['auth'].get(
                'token', {'id': 'fc394f2ab2df4114bde39905f800dc57'}).get('id')
            token['tenant'] = dict()
            token['tenant']['description'] = None
            token['tenant']['enabled'] = True
            token['tenant']['id'] = req['auth'].get(
                'tenantId', 'fc394f2ab2df4114bde39905f800dc57')
            token['tenant']['name'] = "tenantName"

            ret['access']['user'] = dict()
            user = ret['access']['user']
            user['username'] = req.get('username', "username")
            user['name'] = "tenantName"
            user['roles_links'] = list()
            user['id'] = token['tenant'].get(
                'id', "fc394f2ab2df4114bde39905f800dc57")
            user['roles'] = [{'name': 'Member'}]

            ret['access']['region_name'] = "RegionOne"

            ret['access']['serviceCatalog'] = [{
                "endpoints": [
                    {
                        "adminURL": "http://%s:%s/v2.1/%s" % (get_host(request), self.api.port + 3774, user['id']),
                        "region": "RegionOne",
                        "internalURL": "http://%s:%s/v2.1/%s" % (get_host(request), self.api.port + 3774, user['id']),
                        "id": "2dad48f09e2a447a9bf852bcd93548ef",
                        "publicURL": "http://%s:%s/v2.1/%s" % (get_host(request), self.api.port + 3774, user['id'])
                    }
                ],
                "endpoints_links": [],
                "type": "compute",
                "name": "nova"
            },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s/v2.0" % (get_host(request), self.api.port),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s/v2.0" % (get_host(request), self.api.port),
                            "id": "2dad48f09e2a447a9bf852bcd93543fc",
                            "publicURL": "http://%s:%s/v2" % (get_host(request), self.api.port)
                        }
                    ],
                    "endpoints_links": [],
                    "type": "identity",
                    "name": "keystone"
            },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s" % (get_host(request), self.api.port + 4696),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s" % (get_host(request), self.api.port + 4696),
                            "id": "2dad48f09e2a447a9bf852bcd93548cf",
                            "publicURL": "http://%s:%s" % (get_host(request), self.api.port + 4696)
                        }
                    ],
                    "endpoints_links": [],
                    "type": "network",
                    "name": "neutron"
            },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s" % (get_host(request), self.api.port + 4242),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s" % (get_host(request), self.api.port + 4242),
                            "id": "2dad48f09e2a447a9bf852bcd93548cf",
                            "publicURL": "http://%s:%s" % (get_host(request), self.api.port + 4242)
                        }
                    ],
                    "endpoints_links": [],
                    "type": "image",
                    "name": "glance"
            },
                {
                    "endpoints": [
                        {
                            "adminURL": "http://%s:%s/v1/%s" % (get_host(request), self.api.port + 3004, user['id']),
                            "region": "RegionOne",
                            "internalURL": "http://%s:%s/v1/%s" % (get_host(request), self.api.port + 3004, user['id']),
                            "id": "2dad48f09e2a447a9bf852bcd93548bf",
                            "publicURL": "http://%s:%s/v1/%s" % (get_host(request), self.api.port + 3004, user['id'])
                        }
                    ],
                    "endpoints_links": [],
                    "type": "orchestration",
                    "name": "heat"
            }
            ]

            ret['access']["metadata"] = {
                "is_admin": 0,
                "roles": [
                    "7598ac3c634d4c3da4b9126a5f67ca2b"
                ]
            },
            ret['access']['trust'] = {
                "id": "394998fa61f14736b1f0c1f322882949",
                "trustee_user_id": "269348fdd9374b8885da1418e0730af1",
                "trustor_user_id": "3ec3164f750146be97f21559ee4d9c51",
                "impersonation": False
            }
            return Response(json.dumps(ret), status=200,
                            mimetype='application/json')

        except Exception as ex:
            logging.exception("Keystone: Get token failed.")
            return str(ex), 500


class KeystoneGetTokenv3(Resource):
    """
    Returns a static keystone token.
    We don't do any validation so we don't care.
    """

    def __init__(self, api):
        self.api = api

    def post(self):
        """
        List API entrypoints.

        This is hardcoded. For a working "authentication" use these ENVVARS:

        * OS_AUTH_URL=http://<ip>:<port>/v3
        * OS_IDENTITY_API_VERSION=2.0
        * OS_TENANT_ID=fc394f2ab2df4114bde39905f800dc57
        * OS_REGION_NAME=RegionOne
        * OS_USERNAME=bla
        * OS_PASSWORD=bla

        :return: Returns an openstack style response for all entrypoints.
        :rtype: :class:`flask.response`
        """

        LOG.debug("API CALL: %s POST" % str(self.__class__.__name__))
        try:
            ret = dict()
            req = json.loads(request.data)
            ret['token'] = dict()
            token = ret['token']

            token['issued_at'] = "2014-01-30T15:30:58.819Z"
            token['expires_at'] = "2999-01-30T15:30:58.819Z"
            token['methods'] = ["password"]
            token['extras'] = dict()
            token['user'] = dict()
            user = token['user']
            user['id'] = req['auth'].get(
                'token', {'id': 'fc394f2ab2df4114bde39905f800dc57'}).get('id')
            user['name'] = "tenantName"
            user['password_expires_at'] = None
            user['domain'] = {"id": "default", "name": "Default"}
            token['audit_ids'] = ["ZzZwkUflQfygX7pdYDBCQQ"]

            # project
            token['project'] = {
                "domain": {
                    "id": "default",
                    "name": "Default"
                },
                "id": "8538a3f13f9541b28c2620eb19065e45",
                "name": "tenantName"
            }

            # catalog
            token['catalog'] = [{
                "endpoints": [
                    {
                        "url": "http://%s:%s/v2.1/%s" % (get_host(request), self.api.port + 3774, user['id']),
                        "region": "RegionOne",
                        "interface": "public",
                        "id": "2dad48f09e2a447a9bf852bcd93548ef"
                    }
                ],
                "id": "2dad48f09e2a447a9bf852bcd93548ef",
                "type": "compute",
                "name": "nova"
            },
                {
                    "endpoints": [
                        {
                            "url": "http://%s:%s/v2.0" % (get_host(request), self.api.port),
                            "region": "RegionOne",
                            "interface": "public",
                            "id": "2dad48f09e2a447a9bf852bcd93543fc"
                        }
                    ],
                    "id": "2dad48f09e2a447a9bf852bcd93543fc",
                    "type": "identity",
                    "name": "keystone"
            },
                {
                    "endpoints": [
                        {
                            "url": "http://%s:%s" % (get_host(request), self.api.port + 4696),
                            "region": "RegionOne",
                            "interface": "public",
                            "id": "2dad48f09e2a447a9bf852bcd93548cf"
                        }
                    ],
                    "id": "2dad48f09e2a447a9bf852bcd93548cf",
                    "type": "network",
                    "name": "neutron"
            },
                {
                    "endpoints": [
                        {
                            "url": "http://%s:%s" % (get_host(request), self.api.port + 4242),
                            "region": "RegionOne",
                            "interface": "public",
                            "id": "2dad48f09e2a447a9bf852bcd93548cf"
                        }
                    ],
                    "id": "2dad48f09e2a447a9bf852bcd93548cf",
                    "type": "image",
                    "name": "glance"
            },
                {
                    "endpoints": [
                        {
                            "url": "http://%s:%s/v1/%s" % (get_host(request), self.api.port + 3004, user['id']),
                            "region": "RegionOne",
                            "interface": "public",
                            "id": "2dad48f09e2a447a9bf852bcd93548bf"
                        }
                    ],
                    "id": "2dad48f09e2a447a9bf852bcd93548bf",
                    "type": "orchestration",
                    "name": "heat"
            }
            ]
            return Response(json.dumps(ret), status=201,
                            mimetype='application/json')

        except Exception as ex:
            logging.exception("Keystone: Get token failed.")
            return str(ex), 500
