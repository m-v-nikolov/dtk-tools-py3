import logging
import os

import pandas as pd

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer
from plot import plot_by_channel

logger = logging.getLogger(__name__)

def default_plot_fn(df, ax):
    grouped = df.groupby(level=['group'], axis=1)
    m = grouped.mean()
    m.plot(ax=ax, legend=True)


class TimeseriesAnalyzer(BaseAnalyzer):

    plot_name = 'ChannelPlots'
    data_group_names = ['group', 'sim_id', 'channel']
    ordered_levels = ['channel', 'group', 'sim_id']
    output_file = 'timeseries.csv'

    def __init__(self, filename=os.path.join('output', 'InsetChart.json'), filter_function=lambda md: True,
                 select_function=lambda ts: pd.Series(ts), group_function=lambda k, v: k, plot_function=default_plot_fn,
                 channels=['Statistical Population',
                           'Rainfall', 'Adult Vectors',
                           'Daily EIR', 'Infected',
                           'Parasite Prevalence'], saveOutput=False):
        super(TimeseriesAnalyzer, self).__init__()
        self.filenames = [filename]
        self.channels = channels
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function
        self.plot_function   = plot_function
        self.saveOutput = saveOutput

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def validate_channels(self, keys):
        self.channels = [c for c in self.channels if c in keys] if self.channels else keys

    def get_channel_data(self, data_by_channel, header=None):
        channel_series = [self.select_function(data_by_channel[channel]["Data"]) for channel in self.channels]
        return pd.concat(channel_series, axis=1, keys=self.channels)

    def apply(self, parser):
        data = parser.raw_data[self.filenames[0]]
        data_by_channel = data['Channels']
        self.validate_channels(data_by_channel.keys())
        channel_data = self.get_channel_data(data_by_channel, data['Header'])
        channel_data.group = self.group_function(parser.sim_id, parser.sim_data)
        channel_data.sim_id = parser.sim_id
        return channel_data

    def combine(self, parsers):
        logger.debug('Gathering selected data from parser threads...')
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        logger.debug('Combining selected data...')
        combined = pd.concat(selected, axis=1, 
                             keys=[(d.group, d.sim_id) for d in selected], 
                             names=self.data_group_names)
        logger.debug('Re-ordering multi-index levels...')
        self.data = combined.reorder_levels(self.ordered_levels, axis=1).sortlevel(axis=1)

    def finalize(self):
        self.plot_channel_on_axes = lambda channel, ax: self.plot_function(self.data[channel].dropna(), ax)
        if self.saveOutput:
            self.data.to_csv(self.output_file)

    def plot(self):
        plot_by_channel(self.plot_name, self.channels, self.plot_channel_on_axes)
        import matplotlib.pyplot as plt
        plt.show()

