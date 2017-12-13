import logging
from abc import abstractmethod
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)


class BaseComparisonAnalyzer(BaseAnalyzer):
    """
    A class to represent the interface of all analyzers that compare simulation output to a reference, e.g. calibration.
    """

    @abstractmethod
    def __init__(self, site, weight=1, compare_fn=lambda s: True):
        super(BaseComparisonAnalyzer, self).__init__()  # self.data = None
        self.site = site
        self.weight = weight
        self.compare_fn = compare_fn

        self.name = self.__class__.__name__

        self.reference = None  # site-specific reference data for comparison
        self.result = None  # result of simulation-to-reference comparison
        self.data = None

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

    def compare(self, sample):
        """
        Assess the result per sample, e.g. the log-likelihood,
        of a comparison between simulation and reference data.
        """
        return self.compare_fn(sample)

    def finalize(self):
        """
        Calculate the comparison output
        """
        self.result = self.data.apply(self.compare)
        logger.debug(self.result)

    @classmethod
    @abstractmethod
    def plot_comparison(cls, fig, data, **kwargs):
        """
        Plot data onto figure according to logic in derived classes
        """
        pass