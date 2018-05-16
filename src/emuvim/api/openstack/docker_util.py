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
from docker import APIClient
import time
import re


def docker_container_id(container_name):
    """
    Uses the container name to return the container ID.

    :param container_name: The full name of the docker container.
    :type container_name: ``str``
    :return: Returns the container ID or None if the container is not running or could not be found.
    :rtype: ``dict``
    """
    c = APIClient()
    detail = c.inspect_container(container_name)
    if bool(detail["State"]["Running"]):
        return detail['Id']
    return None


def docker_abs_cpu(container_id):
    """
    Returns the used CPU time since container startup and the system time in nanoseconds and returns the number
    of available CPU cores.

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns a dict with CPU_used in nanoseconds, the current system time in nanoseconds and the number of
        CPU cores available.
    :rtype: ``dict``
    """
    with open('/sys/fs/cgroup/cpuacct/docker/' + container_id + '/cpuacct.usage_percpu', 'r') as f:
        line = f.readline()
    sys_time = int(time.time() * 1000000000)
    numbers = [int(x) for x in line.split()]
    cpu_usage = 0
    for number in numbers:
        cpu_usage += number
    return {'CPU_used': cpu_usage,
            'CPU_used_systime': sys_time, 'CPU_cores': len(numbers)}


def docker_mem_used(container_id):
    """
    Bytes of memory used from the docker container.

    Note: If you have problems with this command you have to enable memory control group.
    For this you have to add the following kernel parameters: `cgroup_enable=memory swapaccount=1`.
    See: https://docs.docker.com/engine/admin/runmetrics/

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns the memory utilization in bytes.
    :rtype: ``str``
    """
    with open('/sys/fs/cgroup/memory/docker/' + container_id + '/memory.usage_in_bytes', 'r') as f:
        return int(f.readline())


def docker_max_mem(container_id):
    """
    Bytes of memory the docker container could use.

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns the bytes of memory the docker container could use.
    :rtype: ``str``
    """
    with open('/sys/fs/cgroup/memory/docker/' + container_id + '/memory.limit_in_bytes', 'r') as f:
        mem_limit = int(f.readline())
    with open('/proc/meminfo', 'r') as f:
        line = f.readline().split()
    sys_value = int(line[1])
    unit = line[2]
    if unit == 'kB':
        sys_value *= 1024
    if unit == 'MB':
        sys_value *= 1024 * 1024

    if sys_value < mem_limit:
        return sys_value
    else:
        return mem_limit


def docker_mem(container_id):
    """
    Calculates the current, maximal and percentage usage of the specified docker container.

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns a dictionary with the total memory usage, the maximal available memory and the percentage
        memory usage.
    :rtype: ``dict``
    """
    out_dict = dict()
    out_dict['MEM_used'] = docker_mem_used(container_id)
    out_dict['MEM_limit'] = docker_max_mem(container_id)
    out_dict['MEM_%'] = float(out_dict['MEM_used']) / \
        float(out_dict['MEM_limit'])
    return out_dict


def docker_abs_net_io(container_id):
    """
    Network traffic of all network interfaces within the controller.

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns the absolute network I/O till container startup, in bytes. The return dict also contains the
        system time.
    :rtype: ``dict``
    """
    c = APIClient()
    command = c.exec_create(container_id, 'ifconfig')
    ifconfig = c.exec_start(command['Id'])
    sys_time = int(time.time() * 1000000000)

    in_bytes = 0
    m = re.findall('RX bytes:(\d+)', str(ifconfig))
    if m:
        for number in m:
            in_bytes += int(number)
    else:
        in_bytes = None

    out_bytes = 0
    m = re.findall('TX bytes:(\d+)', str(ifconfig))
    if m:
        for number in m:
            out_bytes += int(number)
    else:
        out_bytes = None

    return {'NET_in': in_bytes, 'NET_out': out_bytes, 'NET_systime': sys_time}


def docker_block_rw(container_id):
    """
    Determines the disk read and write access from the controller since startup.

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns a dictionary with the total disc I/O since container startup, in bytes.
    :rtype: ``dict``
    """
    with open('/sys/fs/cgroup/blkio/docker/' + container_id + '/blkio.throttle.io_service_bytes', 'r') as f:
        read = f.readline().split()
        write = f.readline().split()
    rw_dict = dict()
    rw_dict['BLOCK_systime'] = int(time.time() * 1000000000)
    if len(read) < 3:
        rw_dict['BLOCK_read'] = 0
    else:
        rw_dict['BLOCK_read'] = read[2]
    if len(write) < 3:
        rw_dict['BLOCK_write'] = 0
    else:
        rw_dict['BLOCK_write'] = write[2]
    return rw_dict


def docker_PIDS(container_id):
    """
    Determines the number of processes within the docker container.

    :param container_id: The full ID of the docker container.
    :type container_id: ``str``
    :return: Returns the number of PIDS within a dictionary.
    :rtype: ``dict``
    """
    with open('/sys/fs/cgroup/cpuacct/docker/' + container_id + '/tasks', 'r') as f:
        return {'PIDS': len(f.read().split('\n')) - 1}


def monitoring_over_time(container_id):
    """
    Calculates the cpu workload and the network traffic per second.

    :param container_id: The full docker container ID
    :type container_id: ``str``
    :return: A dictionary with disk read and write per second, network traffic per second (in and out),
        the cpu workload and the number of cpu cores available.
    :rtype: ``dict``
    """
    first_cpu_usage = docker_abs_cpu(container_id)
    first = docker_abs_net_io(container_id)
    first_disk_io = docker_block_rw(container_id)
    time.sleep(1)
    second_cpu_usage = docker_abs_cpu(container_id)
    second = docker_abs_net_io(container_id)
    second_disk_io = docker_block_rw(container_id)

    # Disk access
    time_div = (int(second_disk_io['BLOCK_systime']
                    ) - int(first_disk_io['BLOCK_systime']))
    read_div = int(second_disk_io['BLOCK_read']) - \
        int(first_disk_io['BLOCK_read'])
    write_div = int(second_disk_io['BLOCK_write']) - \
        int(first_disk_io['BLOCK_write'])
    out_dict = {'BLOCK_read/s': int(read_div * 1000000000 / float(time_div) + 0.5),
                'BLOCK_write/s': int(write_div * 1000000000 / float(time_div) + 0.5)}

    # Network traffic
    time_div = (int(second['NET_systime']) - int(first['NET_systime']))
    in_div = int(second['NET_in']) - int(first['NET_in'])
    out_div = int(second['NET_out']) - int(first['NET_out'])
    out_dict.update({'NET_in/s': int(in_div * 1000000000 / float(time_div) + 0.5),
                     'NET_out/s': int(out_div * 1000000000 / float(time_div) + 0.5)})

    # CPU utilization
    time_div = (int(second_cpu_usage['CPU_used_systime']
                    ) - int(first_cpu_usage['CPU_used_systime']))
    usage_div = int(second_cpu_usage['CPU_used']) - \
        int(first_cpu_usage['CPU_used'])
    out_dict.update({'CPU_%': usage_div / float(time_div),
                     'CPU_cores': first_cpu_usage['CPU_cores']})
    return out_dict
