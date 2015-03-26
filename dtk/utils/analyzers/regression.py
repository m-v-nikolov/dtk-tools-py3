import os
import json
from collections import defaultdict
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
from pandas.util.testing import assert_frame_equal
from ..core.DTKSetupParser import DTKSetupParser
from timeseries import TimeseriesAnalyzer
from group import group_by_name

class RegressionTestAnalyzer(TimeseriesAnalyzer):

    def __init__(self, filter_function, 
                 channels=[],
                 onlyPlotFailed=True,
                 saveOutput=False):

        TimeseriesAnalyzer.__init__(self,filter_function=filter_function, 
                                    group_function=group_by_name,
                                    plot_function=lambda df,ax: df.plot(ax=ax,legend=True),
                                    channels=channels, 
                                    saveOutput=saveOutput)

        self.onlyPlotFailed=onlyPlotFailed
        setup=DTKSetupParser()
        self.regression_path=os.path.join( setup.get('BINARIES','dll_path'),
                                   '..','..','Regression' )

    def apply(self, parser):
        test_channel_data=TimeseriesAnalyzer.apply(self,parser)
        reference_path=os.path.join(self.regression_path,
                                    parser.sim_data['Config_Name'],
                                    'output',self.filenames[0])

        # TODO: bump this repeated fragment into a few utilities
        #       e.g. read, pandas table construction, and CSV dump
        #       for each of InsetChart (and other?) JSON and Spatial binary
        with open(reference_path) as f:
            data_by_channel=json.loads(f.read())['Channels']
        channel_series = [self.select_function(data_by_channel[channel]["Data"]) for channel in self.channels]
        ref_channel_data = pd.concat(channel_series, axis=1, keys=self.channels)
        ###

        channel_data=pd.concat(dict(test = test_channel_data, reference = ref_channel_data),axis=1)
        channel_data=channel_data.reorder_levels([1,0],axis=1).sortlevel(axis=1)
        channel_data.group = test_channel_data.group
        channel_data.sim_id = test_channel_data.sim_id
        return channel_data

    def combine(self, parsers):
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected,axis=1,keys=[d.group for d in selected],names=['group','channel','regression'])
        self.data=combined.reorder_levels(['group','channel','regression'],axis=1).sortlevel(axis=1)

    def finalize(self):
        results=defaultdict(list)
        ncol = 1+len(self.channels)/4
        nrow = np.ceil(float(len(self.channels))/ncol)
        for group,group_data in self.data.groupby(level=['group'], axis=1):
            R=group_data[group].reorder_levels(['regression','channel'],axis=1).sortlevel(axis=1)
            try:
                assert_frame_equal(R['reference'],R['test'])
                results['Passed'].append(group)
                if self.onlyPlotFailed: continue
            except Exception:
                pass
            results['Failed'].append(group)
            fig=plt.figure(group,figsize=(10,8))
            ax=None
            for (i,channel) in enumerate(self.channels):
                ax=fig.add_subplot(nrow, ncol, i+1, sharex=ax)
                plt.title(channel)
                self.plot_function(group_data[group][channel].dropna(),ax)
            plt.tight_layout()
        print('------------------- Regression summary -------------------')
        for state,tests in results.items():
            print('%d test(s) %s'%(len(tests),state.lower()))
            #if state is not 'Failed': continue
            for test in tests:
                print('  %s'%test)