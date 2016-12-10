import logging

import pandas as pd

from dtk.utils.parsers.malaria_summary import summary_channel_to_pandas

from calibtool.analyzers.BaseSummaryCalibrationAnalyzer import BaseSummaryCalibrationAnalyzer
from calibtool import LL_calculators
from calibtool.analyzers.Helpers import \
    convert_to_counts, age_from_birth_cohort, season_from_time, aggregate_on_index

logger = logging.getLogger(__name__)


class ChannelBySeasonAgeDensityCohortAnalyzer(BaseSummaryCalibrationAnalyzer):
    """
    Compare reference season-, age-, and density-binned reference observations to simulation output.
    """

    filenames = ['output/MalariaSummaryReport_Monthly_Report.json']

    population_channel = 'Average Population by Age Bin'

    def __init__(self, site, weight=1, compare_fn=LL_calculators.dirichlet_multinomial_pandas, **kwargs):
        super(ChannelBySeasonAgeDensityCohortAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data('density_by_age_and_season')

        # Get channels to extract from 'Channel' level of reference MultiIndex
        ref_ix = self.reference.index
        channels_ix = ref_ix.names.index('Channel')
        self.channels = ref_ix.levels[channels_ix].values

        self.seasons = kwargs.get('seasons')

    def apply(self, parser):
        """
        Extract data from output simulation data and accumulate in same bins as reference.
        """

        # Load data from simulation
        data = parser.raw_data[self.filenames[0]]

        # Population by age and time series (to convert parasite prevalence to counts)
        population = summary_channel_to_pandas(data, self.population_channel)

        # Coerce channel data into format for comparison with reference
        channel_data_dict = {}
        for channel in self.channels:

            # Prevalence by density, age, and time series
            channel_data = summary_channel_to_pandas(data, channel)

            # Calculate counts from prevalence and population
            channel_counts = convert_to_counts(channel_data, population)

            # Reset multi-index and perform transformations on index columns
            df = channel_counts.reset_index()
            df = age_from_birth_cohort(df)  # calculate age from time for birth cohort
            df = season_from_time(df, seasons=self.seasons)  # calculate month from time

            # Re-bin according to reference and return single-channel Series
            rebinned = aggregate_on_index(df, self.reference.loc(axis=1)[channel].index, keep=[channel])
            channel_data_dict[channel] = rebinned[channel].rename('Counts')

        sim_data = pd.concat(channel_data_dict.values(), keys=channel_data_dict.keys(), names=['Channel'])
        sim_data = pd.DataFrame(sim_data)  # single-column DataFrame for standardized combine/compare pattern
        sim_data.sample = parser.sim_data.get('__sample_index__')
        sim_data.sim_id = parser.sim_id

        return sim_data
