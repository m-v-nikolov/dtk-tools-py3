import logging
from abc import ABCMeta, abstractmethod

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class BaseComparisonAnalyzer(BaseAnalyzer):
    """
    A class to represent the interface of all analyzers that compare simulation output to a reference, e.g. calibration.
    """

    __metaclass__ = ABCMeta

    compare_fn = lambda ref, sim: 1  # formerly LL_fn

    def __init__(self, name, weight, reference_type):
        super(BaseComparisonAnalyzer, self).__init__()
        self.name = name
        self.weight = weight
        self.reference_type = reference_type

        # CalibSite and its reference are linked in set_site function
        self.site = None
        self.reference = None

        self.result = None  # result of simulation-to-reference comparison

    def set_site(self, site):
        """
        Get the reference data that this analyzer needs from the specified site.
        """
        self.site = site
        self.reference = self.site.get_reference_data(self.reference_type)

    def uid(self):
        """ A unique identifier of site-name and analyzer-name """
        return '_'.join([self.site.name, self.name])

    def filter(self, sim_metadata):
        """
        This analyzer only needs to analyze simulations for the site it is linked to.
        N.B. another instance of the same analyzer may exist with a different site
             and correspondingly different reference data.
        """
        return sim_metadata.get('__site__', False) == self.site.name

    # def set_setup(self, setup):
    #     # TODO: Deprecate with CalibSite.get_reference_data putting the relevant info (e.g. sample times) into Index
    #     pass

    @abstractmethod
    def compare(self):
        """
        Assess the result per sample, e.g. the log-likelihood,
        of a comparison between simulation and reference data.
        """
        pass

    def finalize(self):
        """
        Calculate the comparison output
        """
        self.result = self.data.apply(self.compare)
        logger.debug(self.result)
