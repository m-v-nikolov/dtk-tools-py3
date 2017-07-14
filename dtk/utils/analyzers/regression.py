import json
import os
from collections import defaultdict

import pandas as pd
from pandas.util.testing import assert_frame_equal

from group import group_by_name
from plot import plot_by_channel, plot_lines
from simtools.SetupParser import SetupParser
from timeseries import TimeseriesAnalyzer


class RegressionTestAnalyzer(TimeseriesAnalyzer):

    data_group_names = ['group', 'sim_id', 'regression', 'channel']
    ordered_levels = ['group', 'channel', 'regression', 'sim_id']

    def __init__(self, 
                 filter_function=lambda md: True,
                 channels=[],
                 onlyPlotFailed=True):

        TimeseriesAnalyzer.__init__(self ,filter_function=filter_function, 
                                    group_function=group_by_name('Config_Name'),
                                    plot_function=plot_lines,
                                    channels=channels, 
                                    saveOutput=False)

        self.onlyPlotFailed=onlyPlotFailed
        self.results = defaultdict(list)
        setup = SetupParser()
        self.regression_path = os.path.join(setup.get('dll_root'),
                                            '..', '..', 'Regression')

    def apply(self, parser):
        test_channel_data = TimeseriesAnalyzer.apply(self, parser)

        reference_path = os.path.join(self.regression_path,
                                      parser.sim_data['Config_Name'],
                                      self.filenames[0])
        with open(reference_path) as f:
            data_by_channel = json.loads(f.read())['Channels']
        ref_channel_data = self.get_channel_data(data_by_channel)

        channel_data = pd.concat(dict(test = test_channel_data, reference = ref_channel_data), axis=1)
        channel_data.group = test_channel_data.group
        channel_data.sim_id = test_channel_data.sim_id
        return channel_data

    def verify_equal_output(self, group, group_data):
        df = group_data[group].reorder_levels(['regression','channel','sim_id'], axis=1).sortlevel(axis=1)
        try:
            assert_frame_equal(df['reference'], df['test'])
            self.results['Passed'].append(group)
            return True
        except Exception:
            # TODO: accumulate location of first DataFrame.diff?
            self.results['Failed'].append(group)
        return False

    def finalize(self):

        for group, group_data in self.data.groupby(level=['group'], axis=1):
            if self.verify_equal_output(group, group_data) and self.onlyPlotFailed: 
                continue

            group_data.columns = group_data.columns.droplevel(['group','sim_id'])
            plot_channel_on_axes = lambda channel, ax: self.plot_function(group_data[channel].dropna(), ax)
            plot_by_channel(group, self.channels, plot_channel_on_axes)

        print('------------------- Regression summary -------------------')

        for state, tests in self.results.items():
            print('%d test(s) %s' % (len(tests), state.lower()))
            for test in tests:
                print('  %s' % test)