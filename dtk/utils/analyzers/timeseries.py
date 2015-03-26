import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

def default_plot_fn(df,ax):
    grouped = df.groupby(level=['group'], axis=1)
    m=grouped.mean()
    m.plot(ax=ax,legend=True)

class TimeseriesAnalyzer():

    def __init__(self,
                 filename = 'InsetChart.json',
                 filter_function = lambda md: True, # no filtering based on metadata
                 select_function = lambda ts: pd.Series(ts), # return complete-&-unaltered timeseries
                 group_function  = lambda k,v: k, # group by unique simid-key from parser
                 plot_function   = default_plot_fn,
                 channels = [ 'Statistical Population', 
                              'Rainfall', 'Adult Vectors', 
                              'Daily EIR', 'Infected', 
                              'Parasite Prevalence' ],
                 saveOutput = False):

        self.filenames = [filename]
        self.channels = channels
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function
        self.plot_function   = plot_function
        self.saveOutput = saveOutput

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def apply(self, parser):
        data_by_channel=parser.raw_data[self.filenames[0]]["Channels"]
        self.channels = [c for c in self.channels if c in data_by_channel]
        channel_series = [self.select_function(data_by_channel[channel]["Data"]) for channel in self.channels]
        channel_data = pd.concat(channel_series, axis=1, keys=self.channels)
        channel_data.group = self.group_function(parser.sim_id,parser.sim_data)
        channel_data.sim_id = parser.sim_id
        return channel_data

    def combine(self, parsers):
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected,axis=1,keys=[(d.group,d.sim_id) for d in selected],names=['group','sim_id','channel'])
        self.data=combined.reorder_levels(['channel','group','sim_id'],axis=1).sortlevel(axis=1)

    def finalize(self):
        fig=plt.figure('BasePlots',figsize=(10,8))
        ncol = 1+len(self.channels)/4
        nrow = np.ceil(float(len(self.channels))/ncol)
        ax=None
        for (i,channel) in enumerate(self.channels):
            ax=fig.add_subplot(nrow, ncol, i+1, sharex=ax)
            plt.title(channel)
            self.plot_function(self.data[channel],ax)

        plt.tight_layout()
        if self.saveOutput: self.save()

    def save(self):
        self.data.to_csv('timeseries.csv')
