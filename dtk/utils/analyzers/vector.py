import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from itertools import cycle,islice,repeat,chain

from timeseries import TimeseriesAnalyzer

def default_vectorplot_fn(df,ax):
    grouped = df.groupby(level=['species','group'], axis=1)
    m=grouped.mean()
    nspecies,ngroups=map(len,m.keys().levels)
    colors=list(chain(*[list(repeat(c,ngroups)) for c in islice(cycle(['navy', 'firebrick', 'green']), None, nspecies)]))
    m.plot(ax=ax,legend=True,color=colors,alpha=0.5)

class VectorSpeciesAnalyzer(TimeseriesAnalyzer):

    def __init__(self,
                 filename = 'VectorSpeciesReport.json',
                 filter_function = lambda md: True, # no filtering based on metadata
                 select_function = lambda ts: pd.Series(ts), # return complete-&-unaltered timeseries
                 group_function  = lambda k,v: k,   # group by unique simid-key from parser
                 plot_function   = default_vectorplot_fn,
                 channels = ['Adult Vectors', 'Infectious Vectors', 'Daily EIR'],
                 saveOutput = False):

        TimeseriesAnalyzer.__init__(self,filename,filter_function,select_function,group_function,plot_function,channels,saveOutput)

    def apply(self, parser):
        data=parser.raw_data[self.filenames[0]]
        species_names = data["Header"]["Subchannel_Metadata"]["MeaningPerAxis"][0][0] #?
        data_by_channel=data["Channels"]

        if not self.channels:
            self.channels=data_by_channel.keys()
        else:
            self.channels = [c for c in self.channels if c in data_by_channel]

        species_channel_data={}
        for i,species in enumerate(species_names):
            species_channel_series = [self.select_function(data_by_channel[channel]["Data"][i]) for channel in self.channels]
            species_channel_data[species] = pd.concat(species_channel_series, axis=1, keys=self.channels)

        channel_data = pd.concat(species_channel_data,axis=1)
        channel_data.group = self.group_function(parser.sim_id,parser.sim_data)
        channel_data.sim_id = parser.sim_id

        return channel_data

    def combine(self, parsers):
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected,axis=1,keys=[(d.group,d.sim_id) for d in selected],names=['group','sim_id','species','channel'])
        self.data=combined.reorder_levels(['channel','species','group','sim_id'],axis=1).sortlevel(axis=1)

    def finalize(self):
        ncol = 1+len(self.channels)/4
        nrow = np.ceil(float(len(self.channels))/ncol)
        fig=plt.figure('VectorPlots',figsize=(10,8))
        ax=None
        for (i,channel) in enumerate(self.channels):
            ax=fig.add_subplot(nrow, ncol, i+1, sharex=ax)
            plt.title(channel)
            self.plot_function(self.data[channel].dropna(),ax)
        plt.tight_layout()

    def save(self):
        self.data.to_csv('vector.csv')