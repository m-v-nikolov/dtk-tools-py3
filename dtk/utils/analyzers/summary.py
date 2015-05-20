import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from .timeseries import TimeseriesAnalyzer
from .plot import plot_grouped_lines

class SummaryAnalyzer(TimeseriesAnalyzer):

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

        TimeseriesAnalyzer.__init__(self,filename,filter_function,select_function,group_function,plot_function,channels,saveOutput)

        self.agebins=[]

    def apply(self, parser):
        data_by_channel=parser.raw_data[self.filenames[0]]
        self.agebins = data_by_channel.pop('Age Bins')
        if not self.channels:
            self.channels=data_by_channel.keys()
        else:
            self.channels = [c for c in self.channels if c in data_by_channel]
        channel_series = [self.select_function(data_by_channel[channel]) for channel in self.channels]
        channel_data = pd.concat(channel_series, axis=1, keys=self.channels)
        channel_data.group = self.group_function(parser.sim_id,parser.sim_data)
        channel_data.sim_id = parser.sim_id
        return channel_data

    def finalize(self):
        fig=plt.figure('SummaryPlots',figsize=(10,8))
        ncol = 1+len(self.channels)/4
        nrow = np.ceil(float(len(self.channels))/ncol)
        ax=None
        for (i,channel) in enumerate(self.channels):
            ax=fig.add_subplot(nrow, ncol, i+1, sharex=ax)
            plt.title(channel)
            self.plot_function(self.data[channel],ax)

        #plt.tight_layout()
        if self.saveOutput: self.save()

    def save(self):
        self.data.to_csv('summary.csv')