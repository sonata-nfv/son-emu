#!/usr/bin/env python2
# Copyright (c) 2019 Erik Schilling
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

import logging
import os
import subprocess

import requests
import time
from pipes import quote
from tempfile import NamedTemporaryFile

import urllib3
import yaml

from emuvim.api.osm.osm_component_base import OSMComponentBase
from emuvim.api.util.docker_utils import wrap_debian_like, DOCKER_HOST_IP
from emuvim.api.util.path_utils import get_absolute_path
from emuvim.api.util.process_utils import wait_until
from mininet.log import debug

# disables warnings about verify=False for TLS
# since NBI runs with self-signed certificates this otherwise spams the log
urllib3.disable_warnings()

LOG = logging.getLogger(__name__)


class NBI(OSMComponentBase):

    def __init__(self, net, ip, mongo_ip, kafka_ip, version='latest', name_prefix=''):
        OSMComponentBase.__init__(self)
        self.instance = net.addDocker(
            '{}nbi'.format(name_prefix), ip=ip, dimage=wrap_debian_like('opensourcemano/nbi:%s' % version),
            volumes=['osm_packages:/app/storage'],
            environment={'OSMNBI_DATABASE_URI': 'mongodb://%s:27017' % mongo_ip,
                         'OSMNBI_MESSAGE_HOST': kafka_ip})
        self._ip = self.instance.dcinfo['NetworkSettings']['IPAddress']

    def start(self):
        OSMComponentBase.start(self)
        wait_until('nc -z %s 9999' % self._ip)

    def _osm(self, command):
        prefixed_command = 'osm %s' % command
        debug('executing command: %s\n' % prefixed_command)
        output = subprocess.check_output(prefixed_command, env={'OSM_HOSTNAME': self._ip}, shell=True)
        debug('output: \n%s\n' % output)
        return output

    @staticmethod
    def _create_archive(folder, tmp_file):
        folder = get_absolute_path(folder)
        parent_folder = os.path.dirname(folder)
        basename = os.path.basename(folder)
        subprocess.call('tar czf %s %s' % (quote(tmp_file.name), quote(basename)), cwd=parent_folder, shell=True)

    def onboard_vnfd(self, folder):
        try:
            with NamedTemporaryFile() as tmp_archive:
                self._create_archive(folder, tmp_archive)
                return self._osm('vnfd-create %s' % quote(tmp_archive.name)).strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError('creating vnfd failed: %s' % e.output)

    def onboard_nsd(self, folder):
        try:
            with NamedTemporaryFile() as tmp_archive:
                self._create_archive(folder, tmp_archive)
                return self._osm('nsd-create %s' % quote(tmp_archive.name)).strip()
        except subprocess.CalledProcessError as e:
            raise RuntimeError('creating nsd failed: %s' % e.output)

    def _get_api_token(self):
        token_request = requests.post('https://%s:9999/osm/admin/v1/tokens' % self._ip,
                                      data={'username': 'admin', 'password': 'admin'}, verify=False)
        if not token_request.ok:
            raise RuntimeError('getting token failed with: %s' % token_request.text)
        token = yaml.safe_load(token_request.text)
        return token['id']

    def _api_request_args(self):
        return {'headers': {'Authorization': 'Bearer %s' % self._get_api_token()}, 'verify': False}

    def _api_post_request(self, endpoint, data):
        r = requests.post('https://%s:9999/%s' % (self._ip, endpoint),
                          json=data,
                          **self._api_request_args())
        if not r.ok:
            raise RuntimeError('POST request failed with: %s' % r.text)
        result = yaml.safe_load(r.text)
        return result

    def _api_get_request(self, endpoint):
        r = requests.get('https://%s:9999/%s' % (self._ip, endpoint),
                         **self._api_request_args())
        if not r.ok:
            raise RuntimeError('GET request failed with: %s' % r.text)
        result = yaml.safe_load(r.text)
        return result

    def _api_delete_request(self, endpoint):
        r = requests.delete('https://%s:9999/%s' % (self._ip, endpoint),
                            **self._api_request_args())
        if not r.ok:
            raise RuntimeError('DELETE request failed with: %s' % r.text)

    def register_emulated_api(self, name, api):
        output = self._osm('vim-create --name %s '
                           '--user username '
                           '--password password '
                           '--auth_url http://%s:%d/v2.0 '
                           '--tenant tenantName '
                           '--account_type openstack' % (
                               quote(name),
                               quote(DOCKER_HOST_IP),
                               api.port
                           ))
        vim_id = output.strip()
        while self._api_get_request('osm/admin/v1/vim_accounts/%s' % vim_id)['_admin']['detailed-status'] != 'Done':
            time.sleep(1)
        return vim_id

    def ns_create(self, ns_name, nsd_id, vim_id):
        result = self._api_post_request('osm/nslcm/v1/ns_instances_content', {
            'nsdId': nsd_id,
            'nsName': ns_name,
            # dummy text since this cannot be empty
            'nsDescription': 'created by vim-emu',
            'vimAccountId': vim_id,
        })
        return result['id']

    def ns_get(self, ns_id):
        return self._api_get_request('osm/nslcm/v1/ns_instances_content/%s' % ns_id)

    def ns_action(self, ns_id, vnf_member_index, action, args=None):
        if args is None:
            args = {}
        result = self._api_post_request('osm/nslcm/v1/ns_instances/%s/action' % ns_id, {
            'vnf_member_index': str(vnf_member_index),
            'primitive': action,
            'primitive_params': args,
        })
        return result['id']

    def ns_delete(self, ns_id):
        self._api_delete_request('osm/nslcm/v1/ns_instances_content/%s' % ns_id)

    def ns_list(self):
        return self._api_get_request('osm/nslcm/v1/ns_instances_content')

    @staticmethod
    def _count_all_in_operational_status(ns_list, status):
        return len(filter(lambda x: x['operational-status'] == status, ns_list))

    def ns_wait_until_all_in_status(self, *statuses):
        """Waits for all NSs to be in one of the specified stati.
        Returns a tuple with the counts of the NSs in the invididual
        stati in the same order as the specified stati"""

        LOG.debug('Waiting for all NS to be in status {}'.format(statuses))
        while True:
            ns_list = self.ns_list()
            state = ()
            for status in statuses:
                state += (self._count_all_in_operational_status(ns_list, status),)
            number_correct = sum(state)
            missing = len(ns_list) - number_correct
            if missing == 0:
                break
            logging.debug('waiting for the status of %s services to change to %s' % (missing, statuses))
            time.sleep(1)

        logging.debug('all %d NSs in status %s' % (len(ns_list), statuses))
        return state
