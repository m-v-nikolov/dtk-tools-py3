
# TODO: Generalize this style of CalibAnalyzer as much as possible
#       to minimize repeated code in e.g. PrevalenceByAgeAnalyzer
import logging

import pandas as pd

from calibtool import LL_calculators
from calibtool.analyzers.Helpers import accumulate_agebins_cohort
from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer

logger = logging.getLogger(__name__)

class ClinicalIncidenceByAgeCohortAnalyzer(BaseAnalyzer):

    required_reference_types = ['annual_clinical_incidence_by_age']
    filenames = ['output/MalariaSummaryReport_Annual_Report.json']

    x = 'age_bins'
    y = 'Annual Clinical Incidence by Age Bin'

    data_group_names = ['sample', 'sim_id', 'channel']

    def __init__(self,  weight=1):
        self.name = 'ClinicalIncidenceByAgeCohortAnalyzer'
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
