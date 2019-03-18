import logging
from io import BytesIO

import docker

from emuvim.api.util.path_utils import get_absolute_path


def build_dockerfile_dir(folder, tag):
    dcli = docker.from_env().api
    folder = get_absolute_path(folder)
    build_stream = dcli.build(folder, tag=tag)
    logging.info('Docker build result:')
    for line in build_stream:
        logging.info(line)


def suffix_tag_name(tag, suffix):
    if ":" in tag:
        return "%s_%s" % (tag, suffix)
    return "%s:latest_%s" % (tag, suffix)


def wrap_debian_like(image):
    dcli = docker.from_env().api
    dockerfile = '''
    FROM %s
    RUN apt update -y && apt install -y net-tools iputils-ping iproute
    ''' % image
    f = BytesIO(dockerfile.encode('utf-8'))
    wrapper_name = suffix_tag_name(image, 'containernet_compatible')
    logging.info('wrapping image: %s->%s' % (image, wrapper_name))
    build_stream = dcli.build(fileobj=f, tag=wrapper_name)
    build_result = [line for line in build_stream]
    logging.debug('Docker build result:' + '\n'.join(build_result))
    return wrapper_name


# 172.17.0.1 is the ip of the docker0 interface on the host
DOCKER_HOST_IP = '172.17.0.1'
