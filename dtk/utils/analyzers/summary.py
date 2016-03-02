import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from .timeseries import TimeseriesAnalyzer
from .plot import plot_grouped_lines

class SummaryAnalyzer(TimeseriesAnalyzer):

    plot_name = 'SummaryPlots'
    output_file = 'summary.csv'

    def __init__(self,
                 filename = 'MalariaSummaryReport_AnnualAverage.json',
                 filter_function = lambda md: True, # no filtering based on metadata
                 select_function = lambda ts: pd.Series(ts), # return complete-&-unaltered timeseries
                 group_function  = lambda k,v: k,   # group by unique simid-key from parser
                 plot_function   = plot_grouped_lines,
                 channels = ['Annual EIR', 'PfPR_2to10'],

                             ### TODO: plot quantities versus age ###
                             #,'Average Population by Age Bin', 
                             #'PfPR by Age Bin', 'RDT PfPR by Age Bin', 
                             #'Annual Clinical Incidence by Age Bin', 
                             #'Annual Severe Incidence by Age Bin'],

                 saveOutput = False):

        TimeseriesAnalyzer.__init__(self, filename,
                                    filter_function, select_function,
                                    group_function, plot_function,
                                    channels, saveOutput)

        self.agebins=[]

    def get_channel_data(self, data_by_channel, header=None):
        channel_series = [self.select_function(data_by_channel[channel]) for channel in self.channels]
        return pd.concat(channel_series, axis=1, keys=self.channels)

    def apply(self, parser):
        data_by_channel = parser.raw_data[self.filenames[0]]
        self.agebins = data_by_channel.pop('Age Bins')
        self.validate_channels(data_by_channel.keys())
        channel_data = self.get_channel_data(data_by_channel)
        channel_data.group = self.group_function(parser.sim_id, parser.sim_data)
        channel_data.sim_id = parser.sim_id
        return channel_data