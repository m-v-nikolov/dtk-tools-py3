import logging
import itertools
from collections import OrderedDict

import numpy as np
import pandas as pd

from calibtool import LL_calculators
from calibtool.analyzers.Helpers import json_to_pandas, reorder_sim_data
from calibtool.analyzers.BaseComparisonAnalyzer import BaseComparisonAnalyzer

logger = logging.getLogger(__name__)

# TODO: from site_BFdensity (verify has all been subsumed into class info below?)
# {'name': 'analyze_seasonal_monthly_density_cohort',
#  'reporter': 'Monthly Summary Report',
#  'seasons': {'start_wet': 6, 'peak_wet': 8, 'end_wet': 0},
#  'fields_to_get': ['PfPR by Parasitemia and Age Bin',
#                    'PfPR by Gametocytemia and Age Bin',
#                    'Average Population by Age Bin'],
#  'LL_fn': 'dirichlet_multinomial'}


class PrevalenceByAgeSeasonAnalyzer(BaseComparisonAnalyzer):

    filenames = ['output/MalariaSummaryReport_Monthly_Report.json']

    x = 'age_bins'
    y1 = 'PfPR by Parasitemia and Age Bin'
    y2 = 'PfPR by Gametocytemia and Age Bin'

    data_group_names = ['sample', 'sim_id', 'channel']

    def __init__(self, site, weight=1, compare_fn=LL_calculators.dirichlet_multinomial_pandas):
        super(PrevalenceByAgeSeasonAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data('density_by_age_and_season')

    def apply(self, parser):
        """
        Extract data from output simulation data and accumulate in same bins as reference.
        """

        # Load data from simulations
        data = parser.raw_data[self.filenames[0]]

        # Population dataframe
        population = data['TimeXAgeBin']['Average Population by Age Bin']
        bins = OrderedDict([('Time', [i for i in range(13)]), ('Age Bins', [1000])])
        bin_tuples = list(itertools.product(*bins.values()))
        multi_index = pd.MultiIndex.from_tuples(bin_tuples, names=bins.keys())
        channel_pop = 'Population by Age Bin'
        population = pd.Series(np.array(population).flatten(), index=multi_index, name=channel_pop)

        channel = 'PfPR by Parasitemia and Age Bin'  # TODO: only used in reorder_sim_data?? but both channels??

        # Simulation dataframe
        months = self.reference['Metadata']['months']
        bins = OrderedDict([('Time', [i * 1 for i, _ in enumerate(data['Time']['Annual EIR'])]),
                            ('Age Bins', data['Metadata']['Age Bins']),
                            ('PfPR bins', data['Metadata']['Parasitemia Bins'])])
        simdata1 = [data[type][self.y1] for type in data.keys() if self.y1 in data[type].keys()]
        simdata2 = [data[type][self.y2] for type in data.keys() if self.y2 in data[type].keys()]
        temp_data1 = json_to_pandas(simdata1[0], bins, channel)  # Sim data converted to Pandas
        temp_data1 = reorder_sim_data(temp_data1, self.ref_data, months, self.y1, population)
        temp_data2 = json_to_pandas(simdata2[0], bins, channel)  # Sim data converted to Pandas
        temp_data2 = reorder_sim_data(temp_data2, self.ref_data, months, self.y2, population)
        sim_data = pd.concat([temp_data1, temp_data2])

        sim_data.sample = parser.sim_data.get('__sample_index__')
        sim_data.sim_id = parser.sim_id

        return sim_data

    def combine(self, parsers):
        """
        Combine the simulation data into a single table for all analyzed simulations.
        """

        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected, axis=0,
                         keys=[(d.sim_id, d.sample) for d in selected],
                             names=self.data_group_names)
        combined = combined.reset_index()
        groupByColumns = list(combined.keys()[1:-1])  # Only taking sim_id, Age_Bins, Seasons (if available), PfPR Bins (if available), PfPR Type (if available)
        combined = pd.DataFrame.dropna(combined.groupby(groupByColumns).mean().reset_index())
        del combined['channel']
        self.data = pd.pivot_table(combined, values=combined.keys()[-1], index=list(combined.keys()[1:-1]), columns=combined.keys()[0])
        logger.debug(self.data)

    def compare(self, sample):
        """
        Assess the result per sample, in this case the likelihood
        comparison between simulation and reference data.
        """

        sample = sample.reset_index()
        sample.rename(columns={sample.keys()[-1]: 'sim'}, inplace=True)
        sample['ref'] = self.ref_data.reset_index()['PfPR by Parasitemia and Age Bin']
        sample = sample[sample['sim'] > 0]
        sample = sample[sample['ref'] > 0]

        return self.compare_fn(sample)

    def finalize(self):
        """
        Calculate the output result for each sample.
        """
        self.result = self.data.apply(self.compare)
        logger.debug(self.result)

    def cache(self):
        """
        Return a cache of the minimal data required for plotting sample comparisons
        to reference comparisons.
        """

        # TODO: this is only caching y1 but not y2?

        cache = self.data.copy()
        sample_dicts = [{self.y1:[cache[i][j] for j in range(len(cache[i])) ]} for i in range(len(cache.keys()))] # i cycles through simulation id, y cycles through sim values
        ref_dicts = {self.y1:[self.ref_data[i] for i in range(len(self.ref_data))]}
        logger.debug(sample_dicts)

        return {'sims': sample_dicts, 'reference': ref_dicts, 'axis_names': [self.x, self.y1]}
