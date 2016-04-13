import copy
import logging

logger = logging.getLogger(__name__)


class SiteFunctions(object):
    '''
    A helper to take a set of bare SimConfigBuilder-modifying functions
    and combine them into a single function of the same format
    '''

    def __init__(self, name, setup_functions):
        self.name = name
        self.setup_functions = setup_functions

    def set_calibration_site(self, cb):
        '''
        N.B. The name of this function is chosen to ensure it is applied first
        by ModBuilder.set_mods and other aspects can be over-ridden as needed 
        by sample-point modifications.

        TODO: resolve redundancy with dtk.calibration.study_sites.set_calibration_site
        '''
        metadata = {'__site__': self.name}
        for fn in self.setup_functions:
            md = fn(cb)
            #if md:
            #    metadata.update(md)
        return metadata


class CalibSite(object):

    def __init__(self, name, setup_fn, reference_data, analyzers, analyzer_setups={}):
        self.name = name
        self.setup_fn = setup_fn
        self.reference_data = reference_data
        self.analyzers = []

        if not analyzers:
            raise Exception('Each CalibSite must enable at least one analyzer.')

        logger.info('Setting up %s CalibSite:' % name)
        logger.info('  Analyzers = %s' % [a.name for a in analyzers])
        logger.debug('Reference data:\n  %s' % reference_data)

        for a in analyzers:
            site_analyzer = copy.deepcopy(a)  # ensure unique instance at each site
            
            for ref_type in a.required_reference_types:
                if ref_type not in self.reference_data.keys():
                    raise Exception('Missing reference data %s for analyzer %s'
                                    % (ref_type, a.name))
            try :
                site_analyzer.set_setup(analyzer_setups[a.name])
            except KeyError :
                logger.warn('No analyzer settings provided for %s' % a.name)
            site_analyzer.set_site(self)
            self.analyzers.append(site_analyzer)

    @classmethod
    def from_setup_functions(cls, name, setup_functions, reference_data, analyzers, analyzer_setups):
        setup_fn = SiteFunctions(name, setup_functions).set_calibration_site
        return cls(name, setup_fn, reference_data, analyzers, analyzer_setups)