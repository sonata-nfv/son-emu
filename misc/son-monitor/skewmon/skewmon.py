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
Monitor the skewness of the resource usage probability distribution
and export to a Prometheus Push Gateway
(c) 2017 by Steven Van Rossem <steven.vanrossem@intec.ugent.be>
"""

#!/usr/bin/python3

from time import sleep, time, perf_counter
import math
from prometheus_client import start_http_server, Summary, Histogram, Gauge, Counter, REGISTRY, CollectorRegistry, \
    pushadd_to_gateway, push_to_gateway, delete_from_gateway
import threading
import os
import json

import logging
LOG = logging.getLogger('skewmon')
LOG.setLevel(level=logging.DEBUG)
LOG.addHandler(logging.StreamHandler())


# put env vars in Dockerfile
PUSHGATEWAY_IP = '172.17.0.1'
PUSHGATEWAY_PORT = 9091
PUSHGATEWAY_ADDR = ':'.join([PUSHGATEWAY_IP, str(PUSHGATEWAY_PORT)])


#general settings (ms)
SAMPLE_PERIOD = int(os.environ['SAMPLE_PERIOD'])
TOTAL_PERIOD = int(os.environ['TOTAL_PERIOD'])

# define global variables
registry = CollectorRegistry()
exported_metric = Gauge('skewness', 'Skewness of docker vnf resource usage',
                                              ['vnf_id', 'vnf_name', 'vnf_metric'], registry=registry)

# find the VNFs to monitor
# {metric_shortId: {VNF_NAME:<>,VNF_ID:<>,VNF_METRIC:<>}}

def get_vnfs_to_monitor(config):
    for key in config:
        vnf_name = config[key].get('VNF_NAME')
        vnf_id = config[key].get('VNF_ID')
        vnf_metric = config[key].get('VNF_METRIC')
        yield (vnf_id, vnf_name, vnf_metric)

# export metric to the Prometheus PushGateway
def export_metrics(key=None):
    try:
        pushadd_to_gateway(PUSHGATEWAY_ADDR, job='sonemu-skewmon', registry=registry, grouping_key=key)
    except Exception as e:
        LOG.warning("Pushgateway not reachable: {0}".format(str(e)))

class skewness_monitor():
    def __init__(self, docker_id, docker_name, metric):
        # Prometheus metric to export
        self.prom_skewness = exported_metric
        self.docker_id = docker_id
        self.docker_name = docker_name
        self.vnf_metric = metric

        # https://www.datadoghq.com/blog/how-to-collect-docker-metrics/
        self.cpu_proc_file = '/sys/fs/cgroup/cpuacct/docker/{0}/cpuacct.usage'.format(self.docker_id)
        self.mem_proc_file = '/sys/fs/cgroup/memory/docker/{0}/memory.usage_in_bytes'.format(self.docker_id)
        metric_dict = {'cpu': self.cpu_proc_file,
                       'mem': self.mem_proc_file}

        self.proc_file = metric_dict[metric]

        self.fp = open(self.proc_file)

        #monitoring thread
        self.export_thread = None
        self.monitor_stop = threading.Event()

    # get statistics with certain frequency and export skewness for further analysis
    def _calc_skewness(self):

        cpu_count0 = 0
        time0 = 0

        #milliseconds
        stat_delta = SAMPLE_PERIOD
        sample_T = TOTAL_PERIOD

        data = []
        n = 0

        moment1 = 0
        moment2 = 0
        moment3 = 0

        fp = self.fp

        #collect samples
        for n in range(0,round(sample_T/stat_delta)):
            # first measurement
            if cpu_count0 <= 0 or time0 <= 0:
                time0 = perf_counter()
                cpu_count0 = int(fp.read().strip())
                fp.seek(0)
                sleep(stat_delta/1000)
                continue


            #perf_counter in seconds
            time1 = perf_counter()

            # cpu count in nanoseconds
            cpu_count1 = int(fp.read().strip())
            fp.seek(0)

            cpu_delta = cpu_count1 - cpu_count0
            cpu_count0 = cpu_count1

            time_delta = time1 - time0
            time0 = time1

            #work in nanoseconds
            metric = (cpu_delta / (time_delta * 1e9))

            data.append(metric)

            #running calculation of sample moments
            moment1 += metric
            temp = metric * metric
            moment2 += temp
            moment3 += temp * metric


            sleep(stat_delta/1000)

        # calc skewness
        M1 = (1 / n) * moment1
        M2 = ((1 / n) * moment2) - M1**2
        M3 = ((1 / n) * moment3) - (3 * M1 * ((1 / n) * moment2)) + (2 * M1**3)

        s2 = (math.sqrt(n*(n - 1))/(n - 2)) * (M3 / (M2)**1.5)

        LOG.info("docker_name: {0} metric: {1}".format(self.docker_name, self.vnf_metric))
        LOG.info("Nsamples: {0}".format(n))
        LOG.info("skewness: {0:.2f}".format(s2))
        LOG.info("\n")

        return s2

    def _export_skewness_loop(self, stop_event):
        #loop until flag is set
        while(not stop_event.is_set()):
            try:
                skewness = self._calc_skewness()
                self.prom_skewness.labels(vnf_id=self.docker_id, vnf_name=self.docker_name, vnf_metric=self.vnf_metric)\
                    .set(skewness)
            except ZeroDivisionError as e:
                self.prom_skewness.labels(vnf_id=self.docker_id, vnf_name=self.docker_name, vnf_metric=self.vnf_metric) \
                    .set(float('nan'))
                LOG.warning("{1}: Skewness cannot be calculated: {0}".format(str(e), self.docker_name))
            except Exception as e:
                LOG.warning("Skewness cannot be calculated, stop thread: {0}".format(str(e)))
                self.monitor_stop.set()

        # if while has ended, monitoring thread will stop
        self.prom_skewness.labels(vnf_id=self.docker_id, vnf_name=self.docker_name, vnf_metric=self.vnf_metric) \
            .set(float('nan'))

    #start the monitoring thread
    def start(self):
            if self.export_thread is not None:
                LOG.warning('monitor thread is already running for: {0}'.format(self.docker_name))
                return

            self.export_thread = threading.Thread(target=self._export_skewness_loop, args=(self.monitor_stop,))
            self.export_thread.start()
            LOG.info('started thread: {0}'.format(self.docker_name))

    #stop the monitoring thread
    def stop(self):
        self.monitor_stop.set()


if __name__ == '__main__':

    #started_vnfs {vnf_id:object}
    vnfs_monitored = {}

    # endless loop
    while True:
        #check config.txt for docker ids/names
        configfile = open('/config.txt', 'r')
        config = json.load(configfile)
        vnfs_to_monitor = list(get_vnfs_to_monitor(config))

        #for each new docker id in ENV start thread to monitor skewness
        for vnf_id, vnf_name, vnf_metric in vnfs_to_monitor:
            key = '_'.join([vnf_metric, vnf_id])
            if key not in vnfs_monitored:
                try:
                    vnfs_monitored[key] = skewness_monitor(vnf_id, vnf_name, vnf_metric)
                    vnfs_monitored[key].start()
                except Exception as e:
                    LOG.warning("Monitor cannot be started: {0}".format(str(e)))

         #for each removed docker id ENV, stop export
        for vnf_key in list(vnfs_monitored):
            vnf_keys_to_monitor = ['_'.join([vnf_metric, vnf_id]) for vnf_id, vnf_name, vnf_metric in vnfs_to_monitor]
            if vnf_key not in vnf_keys_to_monitor:
                vnfs_monitored[vnf_key].stop()

                vnf_name = vnfs_monitored[vnf_key].docker_name
                vnf_metric, vnf_id = vnf_key.split('_')
                LOG.info('stop monitored VNFs: {0}'.format(vnfs_monitored[vnf_key].docker_name))
                del vnfs_monitored[vnf_key]

                # remove metric with labels from registry
                # (Push Gateway remembers last pushed value, so this is not so useful)
                # collector = registry._names_to_collectors['skewness']
                # if (vnf_id, vnf_name, vnf_metric) in collector._metrics:
                #     collector.remove(vnf_id, vnf_name, vnf_metric)
                delete_from_gateway(PUSHGATEWAY_ADDR, job='sonemu-skewmon')


        #push to Prometheus gateway
        export_metrics()
        LOG.info('monitored VNFs: {0}'.format([monitor.docker_name for key, monitor in vnfs_monitored.items()]))
        # wait before checking  again
        sleep(TOTAL_PERIOD/1000)