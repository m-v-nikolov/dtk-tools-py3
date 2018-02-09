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


class ChannelByMonthSpatialIncidenceAnalyzer(BaseCalibrationAnalyzer):

    filenames = ['output/InsetChart.json']
    population_channel = 'Statistical Population'

    site_ref_type = 'cc_by_month'

    def __init__(self, site, weight=1, compare_fn=LL_calculators.euclidean_distance_pandas, **kwargs):
        super(ChannelByMonthSpatialIncidenceAnalyzer, self).__init__(site, weight, compare_fn)
        self.reference = site.get_reference_data(self.site_ref_type)

    def apply(self, parser):
        """
        Extract data from output data and accumulate in same bins as reference.
        """

        # Load data from simulation
        data = np.array(parser.raw_data[self.filenames[0]]["Channels"]["New Clinical Cases"]["Data"])

        data = np.array(data[10*365:])

        # aggregate by month (assuming we have 24 months of data, which is "not the smartest..")
        cc_split_monthly = np.array_split(data, 24)

        cc_data = {}
        for i, cc_monthly in enumerate(cc_split_monthly):
            cc_data[i] = np.sum(cc_monthly)

        print(cc_data)

        df = pd.DataFrame.from_dict(cc_data, orient="index")

        df.index.name = 'month'
        df['month'] = df.index
        df = df.reset_index(drop=True)

        df.columns = ['cc', 'month']

        sim_data = df.rename(columns={'cc': 'Counts'})
        sim_data['Channel'] = ['Clinical_Cases'] * len(sim_data)

        sim_data = sim_data.sort_values(['Channel', 'month'])
        sim_data = sim_data.set_index(['Channel', 'month'])

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
        for iax, (obj, group_df) in enumerate(df.groupby('Channel')):
            ax = axs[iax]
            counts = list(group_df['Counts'])
            time = list(group_df['month'])
            months = [calendar.month_abbr[i] for i in time]
            irow, icol = int(iax / ncols), (iax % ncols)
            if irow == 0:
                ax.set_title(obj)
                ax.set_xlabel('month')
            if icol==0:
                ax.set_ylabel('Clinical cases reported')
            if 'reference' in kwargs:
                kwargs2 = kwargs.copy()
                kwargs2.pop('reference')
                ax.plot(time, counts, *args, **kwargs2)
            else:
                ax.plot(time, counts, *args, **kwargs)
            ax.xaxis.set_ticks(time)
            ax.set_xticklabels(months)