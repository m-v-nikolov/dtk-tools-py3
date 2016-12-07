import logging

import pandas as pd

from calibtool import LL_calculators
from calibtool.analyzers.Helpers import summary_channel_to_pandas, convert_to_counts,\
                                        rebin_age_from_birth_cohort, rebin_by_month, reorder_sim_data
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

    channels = ['PfPR by Parasitemia and Age Bin',
                'PfPR by Gametocytemia and Age Bin']

    data_group_names = ['sample', 'sim_id', 'channel']

    def __init__(self, site, weight=1, compare_fn=LL_calculators.dirichlet_multinomial_pandas):
        super(PrevalenceByAgeSeasonAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data('density_by_age_and_season')

        ix = self.reference.index
        self.ref_age_bins = [0] + ix.levels[ix.names.index('Age Bins')].tolist()  # prepend minimum age = 0

    def apply(self, parser):
        """
        Extract data from output simulation data and accumulate in same bins as reference.
        """

        # Load data from simulation
        data = parser.raw_data[self.filenames[0]]

        # Population by age and time series (to convert parasite prevalence to counts)
        population = summary_channel_to_pandas(data, 'Average Population by Age Bin')

        # Prevalence by density, age, and time series
        channel_data_dict = {channel: summary_channel_to_pandas(data, channel) for channel in self.channels}

        # # NEW
        # for channel, channel_data in channel_data_dict.items():
        #
        #     # Normalize prevalence to counts
        #     channel_counts = convert_to_counts(channel_data, population)
        #
        #     # Generate age from birth cohort
        #     birth_cohort_rebinned = rebin_age_from_birth_cohort(channel_counts, self.ref_age_bins)
        #
        #     # Monthly binning
        #     # TODO: generalize to any day-of-year intervals? Discard data not in months of interest from CalibSite?
        #     monthly_binned = rebin_by_month(birth_cohort_rebinned, months=[])
        #
        #     channel_data_dict[channel] = monthly_binned

        # OLD
        # TODO: handle this already in site_Laye reference
        # months = self.reference['Metadata']['months']
        months = ['July', 'September', 'January']
        for channel, channel_data in channel_data_dict.items():
            channel_data_dict[channel] = reorder_sim_data(channel_data, self.reference, months, channel, population)

        sim_data = pd.concat(channel_data_dict.values())
        print(sim_data.head(15))
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
