"""
Prometheus API helper functions
(c) 2016 by Steven Van Rossem <steven.vanrossem@intec.ugent.be>
"""

import urllib2
import ast

prometheus_ip = '0.0.0.0'
prometheus_port = '9090'
prometheus_REST_api = 'http://{0}:{1}'.format(prometheus_ip, prometheus_port)


def query_Prometheus(query):
    url = prometheus_REST_api + '/' + 'api/v1/query?query=' + query
    # logging.info('query:{0}'.format(url))
    req = urllib2.Request(url)
    ret = urllib2.urlopen(req).read()
    ret = ast.literal_eval(ret)
    if ret['status'] == 'success':
        # logging.info('return:{0}'.format(ret))
        try:
            ret = ret['data']['result'][0]['value']
        except:
            ret = None
    else:
        ret = None
    return ret