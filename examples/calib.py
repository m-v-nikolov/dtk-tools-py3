'''
TODO: move to dtk.calibration and update import path in example_calibration.py
'''

import importlib
import logging

import pandas as pd

from calibtool.CalibAnalyzer import CalibAnalyzer
from calibtool.CalibSite import CalibSite

from dtk.calibration import LL_calculators

logger = logging.getLogger(__name__)


class DTKCalibFactory(object):

    @staticmethod
    def get_analyzer(name, weight=1):
        if name == 'ClinicalIncidenceByAgeCohortAnalyzer':
            return ClinicalIncidenceByAgeCohortAnalyzer(name, weight)
        else:
            raise NotImplementedError("Don't recognize CalibAnalyzer: %s" % name)

    @staticmethod
    def get_site(name, analyzers):
        try:
            mod = importlib.import_module('dtk.calibration.study_sites.site_%s' % name)
            return CalibSite.from_setup_functions(
                       name=name,
                       setup_functions=mod.setup_functions,
                       reference_data=mod.reference_data,
                       analyzers=analyzers)
        except ImportError:
            raise NotImplementedError("Don't recognize CalibSite: %s" % name)


# TODO: Generalize this style of CalibAnalyzer as much as possible
#       to minimize repeated code in e.g. PrevalenceByAgeAnalyzer

class ClinicalIncidenceByAgeCohortAnalyzer(CalibAnalyzer):

    required_reference_types = ['annual_clinical_incidence_by_age']
    filenames = ['MalariaSummaryReport_Annual_Report.json']

    x = 'age_bins'
    y = 'Annual Clinical Incidence by Age Bin'

    data_group_names = ['sample', 'sim_id', 'channel']

    def __init__(self, name, weight):
        self.name = name
        self.weight = weight
        self.site = None

    def set_site(self, site):
        '''
        Get the reference data that this analyzer needs from the specified site.
        '''

        self.site = site
        self.reference = self.site.reference_data['annual_clinical_incidence_by_age']

    def filter(self, sim_metadata):
        '''
        This analyzer only needs to analyze simulations for the site it is linked to.
        N.B. another instance of the same analyzer may exist with a different site
             and correspondingly different reference data.
        '''
        return sim_metadata.get('__site__', False) == self.site.name

    def apply(self, parser):
        '''
        Extract data from output data and accumulate in same bins as reference.

        TODO: if we want to plot with the original analyzer age bins,
              we will also need to emit a separate table of parsed data:
              data['Annual Clinical Incidence by Age Bin'], data['Age Bins']
        '''

        data = parser.raw_data[self.filenames[0]]
        ref_age_bins = self.reference['age_bins']

        person_years, counts = accumulate_agebins_cohort(
            data['Annual Clinical Incidence by Age Bin'],
            data['Average Population by Age Bin'],
            data['Age Bins'], ref_age_bins)

        channel_data = pd.DataFrame({'Person Years': person_years,
                                     'Clinical Incidents': counts},
                                    index=ref_age_bins)

        channel_data.index.name = 'age_bins'
        channel_data.sample = parser.sim_data.get('__sample_index__')
        channel_data.sim_id = parser.sim_id

        return channel_data

    def combine(self, parsers):
        '''
        Combine the simulation data into a single table for all analyzed simulations.
        '''

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected, axis=1, 
                             keys=[(d.sample, d.sim_id) for d in selected], 
                             names=self.data_group_names)
        stacked = combined.stack(['sample', 'sim_id'])
        self.data = stacked.groupby(level=['sample', 'age_bins']).mean()
        logger.debug(self.data)

    def compare(self, sample):
        '''
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        '''

        sample['n_obs'] = self.reference['n_obs']
        sample['rates'] = self.reference['Annual Clinical Incidence by Age Bin']
        sample['n_counts'] = (sample.n_obs * sample.rates).astype('int')
        sample = sample[sample['Person Years'] > 0]

        # TODO: vectorize LL_calculators?!
        return LL_calculators.gamma_poisson(
            sample.n_obs.tolist(),
            sample['Person Years'].tolist(),
            sample.n_counts.tolist(),
            sample['Clinical Incidents'].tolist())

    def finalize(self):
        '''
        Calculate the output result for each sample.
        '''
        self.result = self.data.groupby(level='sample').apply(self.compare)
        logger.debug(self.result)

    def cache(self):
        '''
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons.
        '''

        cache = self.data.copy()
        cache = cache[cache['Person Years'] > 0]
        cache['Annual Clinical Incidence by Age Bin'] = cache['Clinical Incidents'] / cache['Person Years']
        cache = cache[['Annual Clinical Incidence by Age Bin']].reset_index(level='age_bins')
        cache.age_bins = cache.age_bins.astype(int)  # numpy.int64 serialization problem with utils.NumpyEncoder
        sample_dicts = [df.to_dict(orient='list') for idx, df in cache.groupby(level='sample', sort=True)]
        logger.debug(sample_dicts)

        return {'sims': sample_dicts, 'reference': self.reference, 'axis_names': [self.x, self.y]}

    def uid(self):
        ''' A unique identifier of site-name and analyzer-name. '''
        return '_'.join([self.site.name, self.name])


# TODO: find a nice home for this and similar functions!
#       this is copied wholesale from dtk.calibration.analyzers.analyze_clinical_incidence_by_age_cohort
def accumulate_agebins_cohort(simdata, average_pop, sim_agebins, raw_agebins) :
    '''
    A function to sum over each year's values in a summary report,
    combining incidence rate and average population 
    to give total counts and population in the reference age binning.
    '''

    glommed_data = [0]*len(raw_agebins)
    simageindex = [-1]*len(sim_agebins)
    yearageindex = [-1]*len(simdata)
    num_in_bin = [0]*len(raw_agebins)

    for i in range(len(simageindex)) :
        for j, age in enumerate(raw_agebins) :
            if sim_agebins[i] < age :
                simageindex[i] = j
                break
    for i in range(len(yearageindex)) :
        for j, age in enumerate(raw_agebins) :
            if i < age :
                yearageindex[i] = j
                break

    for i in range(len(yearageindex)) :
        if yearageindex[i] < 0 :
            continue
        for j in range(len(simageindex)) :
            if simageindex[j] < 0 :
                continue
            glommed_data[simageindex[j]] += simdata[i][j]*average_pop[i][j]
            num_in_bin[simageindex[j]] += average_pop[i][j]

    return num_in_bin, glommed_data