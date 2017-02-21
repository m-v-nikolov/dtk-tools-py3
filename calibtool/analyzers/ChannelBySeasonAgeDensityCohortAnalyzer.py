import logging

import pandas as pd

from dtk.utils.parsers.malaria_summary import summary_channel_to_pandas

from calibtool.analyzers.BaseSummaryCalibrationAnalyzer import BaseSummaryCalibrationAnalyzer, thread_lock
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

            with thread_lock:  # TODO: re-code following block to ensure thread safety (Issue #758)?

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

    @classmethod
    def plot_comparison(cls, fig, data, **kwargs):
        axs = fig.axes
        df = pd.DataFrame.from_dict(data, orient='columns')
        nrows, ncols = len(df.Channel.unique()), len(df.Season.unique())
        if not axs:
            fig.set_size_inches((12, 6))  # override smaller single-panel default from SiteDataPlotter
            axs = [fig.add_subplot(nrows, ncols, iax+1) for iax in range(nrows*ncols)]
        for iax, ((channel, season), group_df) in enumerate(df.groupby(['Channel', 'Season'])):
            ax = axs[iax]
            ages = group_df['Age Bin'].unique()
            irow, icol = (iax / ncols), (iax % ncols)
            if irow == 0:
                ax.set_title(season)
            if irow == (nrows - 1):
                ax.set_xlabel('Age')
            if icol == 0:
                ax.set_ylabel(' '.join(filter(lambda x: 'emia' in x, channel.split()) + ['per uL']))
            for iage, (agebin, agebin_df) in enumerate(group_df.groupby('Age Bin')):
                densities = agebin_df['PfPR Bin'].values
                age_idxs = [iage] * len(densities)
                count_fractions = agebin_df.Counts / agebin_df.Counts.sum()
                if 'reference' in kwargs:
                    scatter_kwargs = dict(facecolor='', lw=2, edgecolor=kwargs.get('color', 'k'), zorder=100)
                else:
                    scatter_kwargs = dict(facecolor=kwargs.get('color', 'k'), lw=0)
                    scatter_kwargs.update({'alpha': 0.1 * kwargs.get('alpha', 1)})
                ax.scatter(age_idxs, range(len(densities)), s=count_fractions * 500, **scatter_kwargs)
                ax.set(xticks=range(len(ages)), xticklabels=ages,
                       yticks=range(len(densities)), yticklabels=densities)
