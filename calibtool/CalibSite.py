import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class SiteFunctions(object):
    """
    A helper to take a set of bare SimConfigBuilder-modifying functions
    and combine them into a single function of the same format
    """

    def __init__(self, name, setup_functions):
        self.name = name
        self.setup_functions = setup_functions

    def set_calibration_site(self, cb):
        """
        N.B. The name of this function is chosen to ensure it is applied first
        by ModBuilder.set_mods and other aspects can be over-ridden as needed 
        by sample-point modifications.
        """
        metadata = {'__site__': self.name}
        for fn in self.setup_functions:
            md = fn(cb)
            # if md:
            #    metadata.update(md)
        return metadata


class CalibSite(object):

    __metaclass__ = ABCMeta

    def __init__(self, name):
        self.name = name
        self.setup_fn = SiteFunctions(self.name, self.get_setup_function()).set_calibration_site
        self.analyzers = self.get_analyzers()

        if not self.analyzers:
            raise Exception('Each CalibSite must enable at least one analyzer.')

        logger.info('Setting up %s CalibSite:', name)
        logger.info('  Analyzers = %s', [a.name for a in self.analyzers])

    @abstractmethod
    def get_reference_data(self, reference_type):
        return {}

    @abstractmethod
    def get_analyzers(self):
        return []

    @abstractmethod
    def get_setup_function(self):
        return []