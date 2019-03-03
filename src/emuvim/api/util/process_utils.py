import logging
import subprocess
import time


def wait_until(cmd):
    logging.debug('waiting for %s\n' % cmd)
    while subprocess.call(cmd, shell=True) != 0:
        time.sleep(1)
