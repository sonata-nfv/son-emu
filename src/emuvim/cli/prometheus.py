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
import requests


# set this to localhost for now
# this is correct for son-emu started outside of a container or as a container with net=host
# TODO if prometheus sdk DB is started outside of emulator, place these
# globals in an external SDK config file?
prometheus_ip = 'localhost'
# when sdk is started with docker-compose, we could use
# prometheus_ip = 'prometheus'
prometheus_port = '9090'
prometheus_REST_api = 'http://{0}:{1}'.format(prometheus_ip, prometheus_port)


def query_Prometheus(query):
    url = prometheus_REST_api + '/' + 'api/v1/query?query=' + query
    # logging.info('query:{0}'.format(url))
    req = requests.get(url)
    ret = req.json()
    if ret['status'] == 'success':
        # logging.info('return:{0}'.format(ret))
        try:
            ret = ret['data']['result'][0]['value']
        except BaseException:
            ret = None
    else:
        ret = None
    return ret
