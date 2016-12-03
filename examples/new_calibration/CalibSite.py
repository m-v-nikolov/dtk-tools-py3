import logging
from abc import ABCMeta, abstractmethod

import copy

from calibtool.CalibSite import SiteFunctions

logger = logging.getLogger(__name__)

class CalibSite:
    __metaclass__ = ABCMeta

    def __init__(self, name):
        self.name = name
        self.setup_fn = SiteFunctions(self.name, self.get_setup_function()).set_calibration_site
        self.reference_data = self.get_reference_data()
        self.analyzers = []
        self.analyzers_setup = self.get_analyzer_setup()

        analyzers = self.get_analyzers()
        if not analyzers:
            raise Exception('Each CalibSite must enable at least one analyzer.')

        logger.info('Setting up %s CalibSite:' % name)
        logger.info('  Analyzers = %s' % [a.name for a in self.analyzers])
        logger.debug('Reference data:\n  %s' % self.reference_data)

        for a in analyzers:
            site_analyzer = copy.deepcopy(a)  # ensure unique instance at each site

            for ref_type in a.required_reference_types:
                if ref_type not in self.reference_data.keys():
                    raise Exception('Missing reference data %s for analyzer %s'
                                    % (ref_type, a.name))
            try:
                site_analyzer.set_setup( self.analyzers_setup[a.name])
            except KeyError:
                logger.warn('No analyzer settings provided for %s' % a.name)
            site_analyzer.set_site(self)
            self.analyzers.append(site_analyzer)

    @abstractmethod
    def get_reference_data(self):
        return {}

    @abstractmethod
    def get_analyzers(self):
        return []

    @abstractmethod
    def get_analyzer_setup(self):
        return {}

    @abstractmethod
    def get_setup_function(self):
        return []