import os

from dtk.utils.analyzers import default_filter_fn, default_select_fn, default_group_fn, default_vectorplot_fn
from dtk.utils.analyzers.TimeSeriesAnalyzer import TimeseriesAnalyzer
import pandas as pd


class VectorSpeciesAnalyzer(TimeseriesAnalyzer):
    plot_name = 'VectorChannelPlots'
    data_group_names = ['group', 'sim_id', 'species', 'channel']
    ordered_levels = ['channel', 'species', 'group', 'sim_id']
    output_file = 'vector.csv'

    def __init__(self,
                 filename=os.path.join('output', 'VectorSpeciesReport.json'),
                 filter_function=default_filter_fn,  # no filtering based on metadata
                 select_function=default_select_fn,  # return complete-&-unaltered timeseries
                 group_function=default_group_fn,  # group by unique simid-key from parser
                 plot_function=default_vectorplot_fn,
                 channels=('Adult Vectors Per Node', 'Percent Infectious Vectors', 'Daily EIR'),
                 saveOutput=False):
        TimeseriesAnalyzer.__init__(self, filename,
                                    filter_function, select_function,
                                    group_function, plot_function,
                                    channels, saveOutput)

    def get_channel_data(self, data_by_channel, selected_channels, header):
        species_channel_data = {}
        species_names = header["Subchannel_Metadata"]["MeaningPerAxis"][0][0]  # ?
        for i, species in enumerate(species_names):
            species_channel_series = [self.select_function(data_by_channel[channel]["Data"][i]) for channel in
                                      selected_channels]
            species_channel_data[species] = pd.concat(species_channel_series, axis=1, keys=selected_channels)
        return pd.concat(species_channel_data, axis=1)
