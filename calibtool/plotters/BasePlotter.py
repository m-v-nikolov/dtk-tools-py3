import os
import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)


class BasePlotter:
    __metaclass__ = ABCMeta

    def __init__(self, combine_sites=True):
        self.combine_sites = combine_sites
        self.iteration_state = None
        self.site_analyzer_names = None

    def get_iteration_directory(self):
        return self.iteration_state.iteration_directory

    def get_plot_directory(self):
        return os.path.join(self.iteration_state.calibration_name, '_plots')

    @property
    def all_results(self):
        return self.iteration_state.all_results

    @abstractmethod
    def visualize(self, iteration_state):
        pass


    @staticmethod
    def combine_by_site(site_name, analyzer_names, results):
        """
        Sum the result values over analyzers performed on the specified site and add SITE_total to results
        :param site_name: The name of the CalibSite
        :param analyzer_names: A list of CalibAnalyzer names corresponding to the site
        :param results: A pandas.DataFrame of results into which to add a combined site-analyzer-result column
        :return: None
        """
        site_analyzers = [site_name + '_' + a for a in analyzer_names]
        logger.debug('site_analyzers: %s', site_analyzers)
        site_total = site_name + '_total'
        results[site_total] = results[site_analyzers].sum(axis=1)
        logger.debug('results[%s]=%s', site_total, results[site_total])