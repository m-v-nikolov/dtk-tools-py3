import os

import pandas as pd

from dtk.utils.analyzers import default_select_fn, default_group_fn, default_filter_fn, plot_by_channel, default_plot_fn
from simtools.Analysis.BaseAnalyzers import BaseAnalyzer


class TimeseriesAnalyzer(BaseAnalyzer):
    data_group_names = ['group', 'sim_id', 'channel']
    ordered_levels = ['channel', 'group', 'sim_id']
    output_file = 'timeseries.csv'

    def __init__(self, filename=os.path.join('output', 'InsetChart.json'), filter_function=default_filter_fn,
                 select_function=default_select_fn, group_function=default_group_fn, plot_function=default_plot_fn,
                 channels=('Statistical Population',
                           'Rainfall', 'Adult Vectors',
                           'Daily EIR', 'Infected',
                           'Parasite Prevalence'), saveOutput=False):
        super(TimeseriesAnalyzer, self).__init__(filenames=(filename,))
        self.channels = set(channels)
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function
        self.plot_function = plot_function
        self.saveOutput = saveOutput

    def filter(self, simulation):
        return self.filter_function(simulation.tags)

    def get_channel_data(self, data_by_channel, selected_channels):
        channel_series = [self.select_function(data_by_channel[channel]["Data"]) for channel in selected_channels]
        return pd.concat(channel_series, axis=1, keys=selected_channels)

    def select_simulation_data(self, data, simulation):
        cdata = data[self.filenames[0]]['Channels']
        selected_channels = self.channels.intersection(cdata.keys()) if self.channels else cdata.keys()
        return self.get_channel_data(cdata, selected_channels)

    def finalize(self, all_data):
        selected = []
        for sim, data in all_data.items():
            # Enrich the data with info
            data.group = self.group_function(sim.id, sim.tags)
            data.sim_id = sim.id
            selected.append(data)

        if len(selected) == 0:
            print("No data have been returned... Exiting...")
            exit()

        # Combining selected data...
        combined = pd.concat(selected, axis=1,
                             keys=[(d.group, d.sim_id) for d in selected],
                             names=self.data_group_names)

        # Re-ordering multi-index levels...
        data = combined.reorder_levels(self.ordered_levels, axis=1).sort_index(axis=1)

        if self.saveOutput:
            data.to_csv(self.output_file)

        def plot_fn(channel, ax):
            self.plot_function(data[channel].dropna(), ax)

        channels = data.columns.levels[0]
        plot_by_channel(channels, plot_fn)
        import matplotlib.pyplot as plt
        plt.legend()
        plt.show()
