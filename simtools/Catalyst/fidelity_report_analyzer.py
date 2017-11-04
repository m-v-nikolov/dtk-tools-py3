import argparse
import json
from collections import defaultdict
import numpy as np
import os
import pandas as pd
import scipy.stats as stats
import matplotlib.pyplot as plt

from simtools.Catalyst.fidelity_html_report import FidelityHTMLReport

from simtools.Catalyst.base_sim_data_analyzer import BaseSimDataAnalyzer, BaseSimDataChannel

class FidelityReportAnalyzer(BaseSimDataAnalyzer):
    """Collection and pre-processing of simulation data."""
    def __init__(self, out_root_dir_path, config_file, campaign_name, demographics_file, experiment_definition,
                 label = None, time_series_step_from = None, time_series_step_to = None, time_series_equal_step_count = False, raw_data = False, debug = False):
        super(FidelityReportAnalyzer, self).__init__(
            output_path=out_root_dir_path,
            demographics_file=demographics_file,
            config_file=config_file,
            campaign_file=campaign_name,
            spatial_channel_names=experiment_definition['spatial_channel_names'],
            inset_channel_names=experiment_definition['inset_channel_names'],
            label=label
        )

        self.exp_def = experiment_definition
        self.sweep_param = experiment_definition['sweep_param']
        self.sweep_values = experiment_definition['sweep_values']
        self.sweep_base_value = experiment_definition['sweep_base_value']

        self.time_series_step_from = time_series_step_from
        self.time_series_step_to = time_series_step_to

        # Adjust label to add from/to parameters to the output dir name
        self.label = self.label or ''
        if time_series_step_from is not None: self.label += '-f{}'.format(time_series_step_from)
        if time_series_step_to is not None: self.label += '-t{}'.format(time_series_step_to)
        self.label = self.label.strip('-')

        self.equal_step_count = time_series_equal_step_count
        self.raw_data = raw_data
        self.debug = debug


    ##########################################
    ### Analyzer interface implementation
    ##########################################

    def filter(self, tags):
        return True

    def apply(self, parser):
        print('calling super apply')
        super(FidelityReportAnalyzer, self).apply(parser)
        print('returned from super apply')

        sd = self.sim_data[parser.sim_id]
        result = sd.to_df(['Run_Number', self.sweep_param])

        return result

    def combine(self, parsers):
        exp_def_path = self.get_result_path('exp_def.json')
        self.exp_def['exp_id'] = self.exp_id
        if not os.path.exists(exp_def_path):
            with open(exp_def_path, 'w') as exp_def_file:
                json.dump(self.exp_def, exp_def_file, sort_keys=True, indent=4)

        # Concatenate data from all sims
        # for k in parsers:
        #     print('*** parser selected data keys: %s' % parsers[k].selected_data.keys())

        # print('parser keys: %s' % [p.selected_data.keys() for p in parsers)
        from pprint import pprint
        print('parsers is a: %s' % type(parsers))
        print("parser keys (%d of them): %s" % (len(parsers.keys()), parsers.keys()))
        # print('selected data keys (%d of them): %s' % (len()))
        print('my id: %s' % id(self))
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        print('***** diagnostics: %s %s %s' % (len(parsers.values()), len(selected), id(self)))

        print('*******')
        for p in parsers.values():
            print('ids in this parser: %s' % p.selected_data.keys())

        max_step_count = max([len(df) for df in selected])
        # in case of 'time step' sweep, inset chart time series will be shorter so we need to expand them to the original size
        if self.equal_step_count:
            # some channels, specified in 'inset_cumulative_channel_names', have cumulative values (vs. snap shot vales) and they have to be downscaled. See adjust_dataframe_length.
            inset_cumulative_channel_names = [] if 'inset_cumulative_channel_names' not in self.exp_def else self.exp_def['inset_cumulative_channel_names']
            selected = [self.adjust_dataframe_length(df, max_step_count, inset_cumulative_channel_names) for df in selected]

        self.result = pd.DataFrame()
        step_from = self.time_series_step_from or 30
        step_to = self.time_series_step_to or max_step_count
        if not (step_from >= 0 and step_from < step_to - 1):
            raise Exception('Invalid from/to arguments: from {} to {}'.format(step_from, step_to))

        # take portion of the simulation dataframe as specified by step_from / step_to arguments.
        self.result = pd.concat([df.iloc[step_from:step_to] for df in selected])

    def finalize(self):
        self.exp_def['duration'] = list(self.sim_data.values())[0].sim_duration

        print('\nCreating reports...')

        # save raw data if needed
        raw_path = self.get_result_path('data_raw.csv')
        if os.path.isfile(raw_path): os.remove(raw_path)
        if self.raw_data:
            self.result.to_csv(raw_path, index=False)
        print('MAKING FIDELITYHTMLREPORT')
        # ck4, self.exp_path should use ... sim.experiment.some_path ?? must be a standard in dtk tools for this
        rpt = FidelityHTMLReport(self.result, self.exp_path, list(self.sim_data.values())[0].demog.node_count, debug = self.debug, **self.exp_def.get_report_instance_args())
        print('MAKING SUMMARY PAGE')
        rpt.create_summary_page()

        # TODO: parallelize, requires some refactoring
        for channel in self.inset_channel_names:
            rpt.create_channel_detail_page(channel)

        # This parallelization approach didn't work likely due to the shared _measure_cache.
        # from multiprocessing.dummy import Pool as ThreadPool
        # pool = ThreadPool(3)
        #
        # pool.map(rpt.create_channel_detail_page, self.inset_channel_names)
        #
        # pool.close()
        # pool.join()

    @staticmethod
    def adjust_dataframe_length(df, new_length, inset_cumulative_channel_names = []):
        """ Adjusts dataframe length by expanding or shrinking dataframe time series.
            Expanding is performed by repeating each value MX number of time"""
        dfx = None
        if 'step' not in df.columns:
            raise Exception('Dataframe is missing "step" column.')

        if df is None or len(df) == 0:
            raise Exception('Dataframe is None or empty')

        if new_length == len(df):
            return df

        if new_length > len(df):
            import math
            # Calculate how many time each row should be repeated.
            mx = int(np.round(new_length / len(df), 0))

            # TODO: modify the method to also ensure representative SE.

            # multiply original dataframe mx times
            dfx = pd.concat([df] * mx)
            dfx = dfx.sort_values(by=['step'])
            # if that is not enough repeate last few values
            if new_length > len(dfx):
                dfx2 = dfx.iloc[[-1] * (new_length - len(dfx))]
                dfx = dfx.append(dfx2)

            dfx = dfx.reset_index()
            # set new 'step' time series based on the new length
            dfx['step'] = pd.Series(range(0, new_length))
            dfx['step'] = dfx['step'].astype(int)

            # downscale cumulative channels
            inset_cumulative_channel_names = inset_cumulative_channel_names  or []
            inset_cumulative_channel_names = ['inset_{}'.format(channel) for channel in inset_cumulative_channel_names]
            for channel in inset_cumulative_channel_names:
                if channel not in dfx.columns.values: continue
                dfx[channel] = dfx[channel]/float(mx)

        elif new_length < len(df):
            raise Exception('Not implemented yet: dataframe is larger than the target length')
        else:
            dfx = df

        if 'index' in dfx.columns:
            del dfx['index']

        # in case dfx hase more than needed take only the first new_length rows
        return dfx.iloc[:new_length]
