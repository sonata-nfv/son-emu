"""
Playground for resource models created by University of Paderborn.
"""
import logging
from emuvim.dcemulator.resourcemodel import BaseResourceModel

LOG = logging.getLogger("rm.upb.simple")
LOG.setLevel(logging.DEBUG)


class UpbSimpleCloudDcApproxRM(BaseResourceModel):
    """
    This will be an example resource model that limits the overall
    resources that can be deployed per data center.
    """
    # TODO Implement resource model issue #12

    def __init__(self, max_cu=32, max_mu=1024):
        self._max_cu = max_cu
        self._max_mu = max_mu
        super(self.__class__, self).__init__()

