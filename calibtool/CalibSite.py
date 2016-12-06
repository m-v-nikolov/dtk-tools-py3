import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class SiteFunctions(object):
    """
    A helper to take a set of bare SimConfigBuilder-modifying functions
    and combine them into a single function of the same format
    """

    def __init__(self, name, setup_functions, verbose=False):
        self.name = name
        self.setup_functions = setup_functions
        self.verbose = verbose

    def set_calibration_site(self, cb):
        """
        N.B. The name of this function is chosen to ensure it is applied first
        by ModBuilder.set_mods and other aspects can be over-ridden as needed 
        by sample-point modifications.
        """
        metadata = {'__site__': self.name}
        for fn in self.setup_functions:
            md = fn(cb)
            if self.verbose and md:
               metadata.update(md)
        return metadata


class CalibSite(object):
    """
    A class to represent the base behavior of a calibration site
    """

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
        """
        Callback function for derived classes to pass site-specific reference data
        that is requested by analyzers by the relevant reference_type.
        """
        return {}

    @abstractmethod
    def get_analyzers(self):
        """
        Derived classes return a list of BaseComparisonAnalyzer instances
        that have been passed a reference to the CalibSite for site-specific analyzer setup.
        """
        return []

    # TODO: expose methods to modify some analyzer properties after construction, e.g. comparison functions and weights.
    # TODO: or alternatively to pass optional arguments through from CalibSite constructor to get_analyzers.

    @abstractmethod
    def get_setup_function(self):
        """
        Derived classes return a list of functions to apply site-specific modifications to the base configuration.
        These are combined into a single function using the SiteFunctions helper class in the CalibSite constructor.
        """
        return []