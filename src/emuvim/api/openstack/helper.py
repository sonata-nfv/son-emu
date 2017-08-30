from urlparse import urlparse
import logging

LOG = logging.getLogger("api.openstack.helper")

def get_host(r):
    try:
        return urlparse(r.base_url).hostname
    except:
        LOG.error("Could not get host part of request URL.")
    return "0.0.0.0"
