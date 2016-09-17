import logging
from abc import ABCMeta

logger = logging.getLogger(__name__)

class BaseAnalyzer(object):
    __metaclass__ = ABCMeta

    required_reference_types = []
    filenames = []
    LL_fn = lambda ref, sim: 1

    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
        self.site = None
        self.setup = {}

    def set_setup(self, setup):
        self.setup = setup

    def filter(self, sim_metadata):
        #return sim_metadata.get('__site__', False) == self.site.name
        return lambda x : True

    def apply(self, parser):
        return {}  # emit sim/reference comparison

    def combine(self, parsers):
        self.data = {}  # combine comparisons by sample-index groups

    def finalize(self):
        pass  # make plots and return summary info