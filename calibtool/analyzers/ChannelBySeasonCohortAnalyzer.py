import calendar
import datetime
import logging
from abc import abstractmethod
import pandas as pd
import numpy as np
from scipy.stats import binom

from calibtool import LL_calculators
from dtk.utils.parsers.malaria_summary import summary_channel_to_pandas
from calibtool.analyzers.BaseCalibrationAnalyzer import BaseCalibrationAnalyzer, thread_lock
from calibtool.analyzers.Helpers import \
    convert_annualized, convert_to_counts, age_from_birth_cohort, aggregate_on_index, aggregate_on_month

logger = logging.getLogger(__name__)


class ChannelBySeasonCohortAnalyzer(BaseCalibrationAnalyzer):
    """
    Base class implementation for similar comparisons of age-binned reference data to simulation output.
    """

    filenames = ['output/ReportVectorStats.csv']
    population_channel = 'Statistical Population'

    site_ref_type = 'entomology_by_season'

    def __init__(self, site, weight=1, compare_fn=LL_calculators.euclidean_distance_pandas, **kwargs):
        super(ChannelBySeasonCohortAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data(self.site_ref_type)

        # ref_channels = self.reference.columns.tolist()
        # if len(ref_channels) != 2:
        #     raise Exception('Expecting two channels from reference data: %s' % ref_channels)
        # try:
        #     ref_channels.pop(ref_channels.index(self.population_channel))
        #     self.channel = ref_channels[0]
        # except ValueError:
        #     raise Exception('Population channel (%s) missing from reference data: %s' %
        #                     (self.population_channel, ref_channels))
        #
        # # Convert reference columns to those needed for likelihood comparison
        # # Trials = Person Years; Observations = Incidents
        # self.reference = pd.DataFrame({'Trials': self.reference[self.population_channel],
        #                                'Observations': (self.reference[self.population_channel]
        #                                                 * self.reference[self.channel])})

    def apply(self, parser):
        """
        Extract data from output data and accumulate in same bins as reference.
        """

        # Load data from simulation
        data = parser.raw_data[self.filenames[0]]

        data = data[365:]
        data['Day'] = data['Time'].apply(lambda x: (x + 1) % 365)
        data = data[['Day', 'Species', 'Population', 'VectorPopulation']]
        data['Vector_per_Human'] = data['VectorPopulation'] / data['Population']
        data = data.groupby(['Day', 'Species'])['Vector_per_Human'].apply(np.mean).reset_index()

        dateparser = lambda x: datetime.datetime.strptime(x, '%j').month
        data['Month'] = data['Day'].apply(lambda x: dateparser(str(x + 1)))
        data = data.groupby(['Month', 'Species'])['Vector_per_Human'].apply(np.mean).reset_index()

        data = data.rename(columns={'Vector_per_Human': 'Counts', 'Species': 'Channel'})
        data = data.sort_values(['Channel', 'Month'])
        data = data.set_index(['Channel', 'Month'])
        channel_data_dict = {}

        for channel in self.site.metadata['species']:

            with thread_lock:  # TODO: re-code following block to ensure thread safety (Issue #758)?

                # Reset multi-index and perform transformations on index columns
                df = data.copy().reset_index()
                df = df.rename(columns={'Counts': channel})
                del df['Channel']

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
        # ax = fig.gca()
        df = pd.DataFrame.from_dict(data, orient='columns')
        nrows, ncols = 1, len(df.Channel.unique())
        fmt_str = kwargs.pop('fmt', None)
        args = (fmt_str,) if fmt_str else ()
        if not axs:
            fig.set_size_inches((12, 6))  # override smaller single-panel default from SiteDataPlotter
            axs = [fig.add_subplot(nrows, ncols, iax+1) for iax in range(nrows*ncols)]
        for iax, (species, group_df) in enumerate(df.groupby('Channel')):
            ax = axs[iax]
            counts = list(group_df['Counts'])
            time = list(group_df['Month'])
            months = [calendar.month_abbr[i] for i in time]
            irow, icol = int(iax / ncols), (iax % ncols)
            if irow == 0:
                ax.set_title(species)
                ax.set_xlabel('Month')
            if icol==0:
                ax.set_ylabel('Vectors per Human')
            if 'reference' in kwargs:
                kwargs2 = kwargs.copy()
                kwargs2.pop('reference')
                ax.plot(time, counts, *args, **kwargs2)
            else:
                ax.plot(time, counts, *args, **kwargs)
            ax.xaxis.set_ticks(time)
            ax.set_xticklabels(months)
