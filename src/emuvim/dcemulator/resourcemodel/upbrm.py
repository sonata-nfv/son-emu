"""
Playground for resource models created by University of Paderborn.
"""
import logging
from emuvim.dcemulator.resourcemodel import BaseResourceModel

LOG = logging.getLogger("upbrm")
LOG.setLevel(logging.DEBUG)


class UpbSimpleCloudDcApproxRM(BaseResourceModel):

    def __init__(self):
        super(self.__class__, self).__init__()

