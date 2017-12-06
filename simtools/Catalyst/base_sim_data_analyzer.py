import glob
import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from collections import defaultdict
from dtk.utils.analyzers.DownloadAnalyzer import DownloadAnalyzer
from simtools.Utilities.COMPSUtilities import get_asset_files_for_simulation_id
# TODO: figure out which version of dtkFileTools to use and how to setup (dtk-tools or DtkTrunk)
import dtk.tools.serialization.dtkFileTools as dft

class BaseSimDataAnalyzer(DownloadAnalyzer):
    """Collect simulation data into SimData objects, one for each simulation."""
    # def __init__(self, out_root_dir_path, demog_path, stdout_filename=None, stdout_filters = [],config_name = 'config.json', campaign_name = 'campaign.json', spatial_channel_names = [], inset_channel_names = [], label = None):
    def __init__(self, output_path, config_file, campaign_file, demographics_file, stdout_filename=None, stdout_filters = [],
                 spatial_channel_names=[], inset_channel_names=[], label=None):
        self.config_file = config_file
        self.campaign_file = campaign_file
        self.demographics_file = demographics_file
        self.stdout_filename = stdout_filename
        self.stdout_filters = stdout_filters
        self.spatial_channel_names = spatial_channel_names
        self.inset_channel_names = inset_channel_names
        self.label = label

        # # TODO add other output data like demog. ummary
        # # input
        # self.filenames = [os.path.basename(config_name)]

        # setup parameters for output file download
        filenames = ['status.txt']
        asset_filenames = []
        if config_file:
            filenames.append(config_file)
        else:
            raise Exception('A config filename must be provided.')

        # These are currently only accessible via AssetManager
        if demographics_file:
            asset_filenames.append(demographics_file)
            self.demographics_file_basename = os.path.basename(demographics_file)
        else:
            raise Exception('A demographics filename must be provided.')

        if campaign_file:
            filenames.append(campaign_file)
        else:
            raise Exception('A campaign filename must be provided.')

        filenames.extend(self.spatial_channel_files)

        if self.inset_channel_names is not None and len(self.inset_channel_names) > 0:
            filenames.append(os.path.join('output', 'InsetChart.json'))

        if self.stdout_filename is not None:
            filenames.append(self.stdout_filename)

        self.asset_filenames = asset_filenames

        filenames = [os.path.normpath(f) for f in filenames]

        # init superclass now that filenames are assembled
        super(BaseSimDataAnalyzer, self).__init__(filenames=filenames, output_path=output_path)

        self.sim_data = defaultdict(SimData)

        self.result = None

    @property
    def spatial_channel_files(self):
        return [os.path.join('output', 'SpatialReport_{}.bin').format(c) for c in self.spatial_channel_names]

    ### Analyzer interface methods

    def initialize(self):
        super(BaseSimDataAnalyzer, self).initialize()

    def filter(self, tags):
        return True

    def apply(self, parser):
        # download self.filenames
        super(BaseSimDataAnalyzer, self).apply(parser)

        output_directory = self.get_sim_folder(parser)
        get_asset_files_for_simulation_id(sim_id=parser.sim_id, paths=self.asset_filenames,
                                          output_directory=output_directory)
        sd = SimData()

        sd.sim_id = parser.sim_id
        sd.sim_path = parser.sim_path

        # Initialize sim sources
        print('Reading sim data for {}\n'.format(parser.sim_id))

        # input
        # ck4, should use raw_data for demographics info, but not a huge deal since we downloaded it
        sd.demog = DemographicsFile(demog_path=os.path.join(output_directory, self.demographics_file_basename))

        # ck4, we need to fix up how the raw_data is read in; this is just bad to force the user to do this
        sd.config = json.loads(parser.raw_data[ os.path.basename(self.config_file) ].getvalue().decode('UTF-8'))['parameters']

        # output

        # ck4, we need to fix up how the raw_data is read in; this is just bad to force the user to do this
        status = parser.raw_data['status.txt'].getvalue().decode('UTF-8')
        done_idx = status.find('Done')
        if done_idx > 0:
            ptt = 'Done - 0:00:00'
            done_str = status[done_idx:done_idx + len(ptt)]
            h, m, s = [int(v) for v in done_str.split('-')[1].strip().split(':')]
            import datetime
            sd.sim_run_time = datetime.timedelta(hours=h, minutes=m, seconds=s)

        if sd.sim_run_time is None:
            print('Unable to parse run time from status.txt')

        sd.spatial_channels = { name : SpatialChannel(parser, name) for name in  self.spatial_channel_names}
        sd.inset_channels = {name: InsetChannel(parser, name) for name in self.inset_channel_names}
        sd.serialized_files = SerializedFiles(parser, sd.step_count)
        if self.stdout_filename is not None:
            sd.stdout = StdOutFile(parser,self.stdout_filename, self.stdout_filters)
        else:
            sd.stdout = None
        self.sim_data[parser.sim_id] = sd

    def combine(self, parsers):
        pass

    def finalize(self):
        pass

    @property
    def inset_channel_columns(self):
        cols = []
        if self.sim_data is not None and len(self.sim_data.values()) > 0:
            cols = [c.column_name for c in self.sim_data.values()[0].inset_channels.values()]

        return cols

    @property
    def spatial_channel_columns(self):
        cols = []
        if self.sim_data is not None and len(self.sim_data.values()) > 0:
            cols = [c.column_name for c in self.sim_data.values()[0].spatial_channels.values()]

        return cols

    @property
    def exp_path(self):
        label = self.label or ''
        # if label was already added to experiment name then ignore it (a case if analyzing an existing experiement)
        if label.strip() == '' or self.exp_name.endswith('_{}'.format(label)): label = ''

        if self.exp_name is None or self.exp_id is None:
            raise Exception('Experiment failed or missing. Cannot construct experiment dir path.')

        # make the reporting directory if it doesn't exist + write out some experiment metadata
        exp_path = os.path.join(self.output_path, 'catalyst_report')
        if not os.path.isdir(exp_path):
            os.makedirs(exp_path)
        return exp_path

    def get_result_path(self, name):

        rpt_path = os.path.join(self.exp_path, name)
        #'{}_{}'.format(self.exp_id, name)

        return rpt_path

    ### Data Analysis Helpers
    # TODO: at later time consider refactoring into a measur specialized class
    # TODO: add the support for aggregating multipe runs (like in fidelity report)
    # TODO: add the support for multiple nodes
    def unstack_result_df_channels_by_sweep_param_values(self, sweep_param, value_columns = None, result_df = None):
        """Takes result df and unstacks channel time series so that each sweep param value has a separate column for each of the channels.
            Usage: Plotting channel time series side by side on the same plot
            Input:
                sweep_param: config parameter used to run sweep experiement
                value_columns: List of inset and/or spatial channels. If not specified the default is all inset/spatial channel columns.
                result_df: If not specified the main result dataframe is used.
                    index: 'step', sweep_param
                    columns: inset and/or spatial channels
            Returns:
                index: step
                columns: tuples: (sweep_param_value, channel) one for each sweep value and channel pair
        """
        value_columns = value_columns or (self.inset_channel_columns + self.spatial_channel_columns)

        df = result_df or self.result
        if df is None: raise Exception('Result dataframe is None.')

        df = df[['step', sweep_param] + value_columns]
        dfp = pd.pivot_table(df, index='step', columns=[sweep_param], values=value_columns)

        return dfp

    ## plotting
    def plot_unstacked_result_df(self, dfp, figsize=(14, 3), rolling_win_size = 30):
        """Plots channel sweep value time series side-by-side on the same plot."""
        fig = plt.figure(figsize=figsize)
        dfp = self.rolling_mean(dfp, rolling_win_size)
        dfp.plot()
        self.save_close_plot(self.result_csv_path.replace('.csv', '.png'), fig)

    def measure_corr(self, dfp_raw, sweep_base_value):
        """Smooths raw time series (not to measure noise) and calculated correlation compared to the base time series.
            Usage: For inset and spatial channels, calculates correlation between the base value time series and other sweep values time series.
            Input: dataframe containing channel columns unstacked by sweep values.
            Returns:list of (correlation, sweep columns) tuples.
        """
        results = []
        dfp = self.rolling_mean(dfp_raw, 30)
        # find the sweep base column
        sweep_base_col = [col for col in dfp.columns if col[1] == sweep_base_value][0]
        # for each remaining column calculate correlation with the base columns
        for sweep_col in dfp.columns[1:]:
            corr = dfp[sweep_base_col].corr(dfp[sweep_col])
            corr = round(corr, 4)
            results.append((corr, sweep_col))

        return results

    def measure_abs_dev_perc(self, dfp_raw, sweep_base_value, do_rolling_mean = True):
        """Smooths raw time series (not to measure noise) and calculated mean abs. deviation percent (MADP) compared to the base time series.
            Usage: For inset and spatial channels, calculates MADP between the base value time series and other sweep values time series.
            Input: dataframe containing channel columns unstacked by sweep values.
            Returns:list of (correlation, sweep columns) tuples.
        """
        results = []
        dfp = self.rolling_mean(dfp_raw, 30) if do_rolling_mean else dfp_raw
        # find the sweep base column
        sweep_base_col = [col for col in dfp.columns if col[1] == sweep_base_value][0]

        # for each remaining column calculate MADP compared to the base time series.
        for sweep_col in dfp.columns[1:]:
            base_mean = np.abs(dfp[sweep_base_col].mean())
            mean_abs_dev = np.abs(dfp[sweep_base_col] - dfp[sweep_col]).mean()
            mean_abs_dev_perc = (mean_abs_dev/ base_mean)
            mean_abs_dev_perc = round(mean_abs_dev_perc, 4)

            results.append((mean_abs_dev_perc, sweep_col))

        return results

    def prepare_measure_result(self, measure_name, measure_data, relation, expected, sweep_param, is_pass_func):
        """Constructs test results sutable for asserting and prining..
            Usage: Transform the output of measure methods by adding test results, expected values and other relevant info.
            Input: measure into (name and data as a list of tuples), expected value(s) sweep info and a validation function
            Returns: list of tuples containing:
             test result, measure name, actual value, relation, expected value, channel name,sweep param, sweep value
        """
        results = []
        # measure_data is a list of tuples containing measure value and sweep columns
        for measure_value, sweep_col in measure_data:
            # note that in this case sweep_col is another tuple containing channel name and sweep value
            channel = sweep_col[0]
            sweep_value =  sweep_col[1]
            # expected value can either be a scalar or a dictionary providing an expected value for each sweep value
            xp_value = expected if isinstance(expected, (int, long, float)) else expected[sweep_value]
            is_pass = is_pass_func(measure_value, xp_value)

            results.append((is_pass, measure_name, measure_value, relation, xp_value, channel, sweep_param, sweep_value))

        return results

    @staticmethod
    def save_close_plot(plot_path, fig):
        """Saves the plot into a .png file and closes plot object (not show UI). """
        plt.savefig(plot_path, bbox_inches='tight')
        if fig:
            plt.close(fig)

    @staticmethod
    def rolling_mean(dfp, rolling_win_size):
        """Rolling-mean on the given dataframe using report default rolling window size."""
        # min_periods = 1 ensures that resutling dataframe doesn't contain NaN values at the begining.
        dfps = dfp.rolling(rolling_win_size, min_periods=1, center=False).mean()

        return dfps

    @staticmethod
    def defaultdict_with_default_None():
        dc = {}
        dc = defaultdict(lambda: None, dc)

        return dc

class SimData:
    def __init__(self):
        self.sim_id = None
        self.sim_path = None
        # input
        self.demog = None
        self.config = None
        self.campaign = None

        # output
        #self.status = None
        self.sim_run_time = None
        self.stdout = None
        #self.stderr = None

        self.serialized_files = None
        self.spatial_channels = None
        self.inset_channels = None

    # TODO
    # dispose method

    # @property
    # def config(self):
    #     if not self._config_json: raise Exception('Config infromation is not available before apply method is invoked.')
    #     return self._config_json

    @property
    def has_serialization(self):
        return 'Serialization_Time_Steps' in self.config and len(self.config['Serialization_Time_Steps']) > 0

    @property
    def expected_step_count(self):
        expected = None
        if self.config is not None:
            expected = int(np.round(self.config['Simulation_Duration'] / self.config['Simulation_Timestep'], 0))

        return expected

    @property
    def actual_step_count(self):
        actual = None
        if self.inset_channels is not None and len(self.inset_channels.keys()) > 0:
            actual = list(self.inset_channels.values())[0].step_count

        return actual

    @property
    def step_count(self):
        return self.actual_step_count or self.expected_step_count


    @property
    def sim_duration(self):
        if not self.config : raise Exception('Config infromation is not available before apply method is invoked.')
        return self.config['Simulation_Duration']

    @property
    def sim_timestep(self):
        return self.config['Simulation_Timestep']

    def to_df(self, config_params = []):
            # TODO:
              # demog_params = []
              # include_spatial_channels = [],
              # include_inset_channels = [],
              # by_node = False):

        df = BaseSimDataChannel.steps_series(self.step_count)
        df['sim_id'] = self.sim_id
        df['total_time'] = self.sim_run_time.total_seconds()

        # Config
        for p in config_params:
            df[p] = self.config[p]

        # spatial
        df_spatial = None
        for c, sc in self.spatial_channels.items():
            if df_spatial is None:
                df_spatial = sc.step_node_df

            df_spatial[sc.column_name] = sc.values_series

        if df_spatial is not None:
            # .agg([np.mean, lambda x: np.std(x, ddof=0)])
            df_spatial = df_spatial.groupby(['step']).agg(['mean', 'std'])
            del df_spatial['node_id']
            df_spatial = df_spatial.reset_index()
            spatial_cols = [['{}'.format(c), '{}_std'.format(c)] for c in self.spatial_channels.keys()]
            spatial_cols = [item for sublist in spatial_cols for item in sublist]
            df_spatial.columns = ['step'] + spatial_cols

            for c in spatial_cols:
                df[SpatialChannel.spatial_column(c)] = df_spatial[c]

        # inset
        for c, sc in self.inset_channels.items():
            df['inset_{}'.format(c)] = sc.values_series

        return df

class DemographicsFile():
    def __init__(self, demog_path, data=None):
        if data:
            self.json = data
            self.demog_path = None
        else:
            self.demog_path = demog_path
            with open(demog_path) as demog_file:
                self.json = json.load(demog_file)

        self.node_count = len(self.json['Nodes'])

    @property
    def node_ids(self):
        return [node['NodeID'] for node in self.json['Nodes']]

    @property
    def locations(self):
        return {node['NodeID']: (node['NodeAttributes']['Latitude'], node['NodeAttributes']['Longitude']) for node in self.json['Nodes']}

    @property
    def nodes_pop(self):
        if not self.json: raise Exception('Demographics information is not available before apply method is invoked.')
        return DemographicsFile.nodes_pop_from_json(self.json)

    @staticmethod
    def nodes_pop_from_json(demog_json):
        init_pop = 0
        try:
            init_pop = demog_json['Defaults']['NodeAttributes']['InitialPopulation']
        except:
            pass

        nodes_pop = BaseSimDataAnalyzer.defaultdict_with_default_None()
        for nd in demog_json['Nodes']:
            node_id = nd['NodeID']
            pop = None
            try:
                pop = nd['NodeAttributes']['InitialPopulation']
            except:
                pass

            nodes_pop[node_id] = pop or init_pop

        return nodes_pop

class StdOutFile():
    def __init__(self, parser, stdout_filename, filters):
        """
        Get lines which contain any string in filters list from StdOut file
        :param parser: TODO: don't know what goes here
        :param stdout_filename: Filename to parse for matching lines
        :param filters: List of strings to use for matching StdOut lines
        """
        self.stdout_path = os.path.join(parser.sim_path, stdout_filename)
        self.content = []
        with open (self.stdout_path) as f:
            for line in f:
                for target in filters:
                    if target in line:
                        self.content.append(line)
                        break

class SerializedFiles():
    def __init__(self, parser, step_count, file_pattern = 'state-{}.dtk'):
        self.parser = parser
        self.step_count = step_count
        self.file_pattern = file_pattern

        self.paths = SerializedFiles.get_file_paths(os.path.join(self.parser.sim_path, 'output'))

        ### Extracted info

        ## Population info
        # self.node_human_count[node_id][step]
        step_dict = {}
        step_dict = defaultdict(lambda: None, step_dict)
        self.node_human_count = defaultdict(lambda : step_dict)

        # TODO
        # extract age male female (number of) and compare as sampling rate chnages
        # individual weights
        # age buckets

        # read individuals count from serialized files if they exist
        if len(self.paths) > 0:
            for t in range(self.step_count + 1):
                state_file_path = os.path.join(self.parser.sim_path, 'output', self.file_pattern).format(str(t).zfill(5))
                if state_file_path not in self.paths: continue
                state_file = dft.read(filename = state_file_path)
                for node in state_file.nodes:
                    if node.externalId not in self.node_human_count.keys():
                        self.node_human_count[node.externalId] = BaseSimDataAnalyzer.defaultdict_with_default_None()
                    self.node_human_count[node.externalId][t] = len(node.individualHumans)

    # @property
    # def paths(self):
    #     if not self.file_paths:
    #         self.file_paths = SerializedFiles.get_file_paths(os.path.join(self.parser.sim_dir, 'output'))
    #
    #     return self.file_paths

    @staticmethod
    def get_file_paths(dir_path):
        ptt = os.path.join(dir_path, 'state-[0-9][0-9][0-9][0-9][0-9].dtk')
        ser_file_paths = glob.glob(ptt)
        return ser_file_paths

class BaseSimDataChannel(object):
    def __init__(self, parser, name, column_name, file_name):
        self.parser = parser
        self.name = name
        self.column_name = column_name
        self.file_name = os.path.join('output', file_name)

    @property
    def step_count(self):
        raise Exception('Not implemented')

    @property
    def values_series(self):
        raise Exception('Not implemented')

    def to_df(self):
        raise Exception('Not implemented')

    def is_valid(self):
        raise Exception('Not implemented')
    #
    # @property
    # def file_name(self):
    #     raise Exception('Not implemented')

    @staticmethod
    def steps_series(step_count):
        steps = range(step_count)
        df = pd.DataFrame({'step': steps})

        return df

class SpatialChannel(BaseSimDataChannel):
    def __init__(self, parser, name):
        super(SpatialChannel, self).__init__(parser, name, SpatialChannel.spatial_column(name), 'SpatialReport_{}.bin'.format(name))

    # BaseSimDataChannel methods

    @property
    def step_count(self):
        return self.parser.raw_data[self.file_name]['n_tstep']

    @property
    def values_series(self):
        row_count = self.step_count * self.node_count
        values = self.parser.raw_data[self.file_name]['data']
        values = values.reshape(row_count)

        return pd.Series(values)

    def to_df(self):
        df = self.step_node_df
        df[self.column_name] = self.values_series

        return df

    def is_valid(self):
        # TODO: add some validation logic
        return True
    #
    # @property
    # def file_name(self):
    #     return os.path.join('output', 'SpatialReport_{}.bin').format(self.name)

    # Spatial channel methods

    @property
    def node_count(self):
        return self.parser.raw_data[self.file_name]['n_nodes']


    @property
    def node_ids(self):
        return list(self.parser.raw_data[self.file_name]['nodeids'])

    def node_value(self, step, node_id):
        n = self.node_ids.index(node_id)
        return self.parser.raw_data[self.file_name]['data'][step][n]

    @property
    def step_node_df(self):
        row_count = self.step_count * self.node_count

        steps = range(self.step_count)
        steps = np.asarray([[t] * self.node_count for t in steps])
        steps = steps.reshape(row_count)

        nodes = self.node_ids * self.step_count

        df = pd.DataFrame({'step': steps})
        df['node_id'] = nodes

        return df

    @staticmethod
    def spatial_column(name):
        return 'spatial_{}'.format(name)

class JsonChannel(BaseSimDataChannel):
    def __init__(self, parser, name, column_name, file_name):
        super(JsonChannel, self).__init__(parser, name, column_name, file_name)

    # ck4, need to fix up the getvalue thing; should be in OutputParser
    @property
    def _data(self):
        return json.loads(self.parser.raw_data[self.file_name].getvalue().decode('UTF-8'))['Channels'][self.name]['Data']

    # ck4, need to fix up the getvalue thing; should be in OutputParser
    @property
    def _header(self):
        return json.loads(self.parser.raw_data[self.file_name].getvalue().decode('UTF-8'))['Header']

    # BaseSimDataChannel methods

    @property
    def step_count(self):
        return len(self._data)

    @property
    def values_series(self):
        return pd.Series(self._data)

    def to_df(self):
        df = BaseSimDataChannel.steps_series(self.step_count)
        #steps = range(self.step_count)
        #df = pd.DataFrame({'step': steps})
        df[self.column_name] = self.values_series

        return df

    def is_valid(self):
        # TODO: add some validation logic
        return True

class InsetChannel(JsonChannel):
    def __init__(self, parser, name):
        super(InsetChannel, self).__init__(
            parser,
            name,
            'inset_{}'.format(name),
            'InsetChart.json'
        )

class VectorSpeciesChannel(JsonChannel):
    def __init__(self, parser, name):
        super(VectorSpeciesChannel, self).__init__(
            parser,
            name,
            'vector_species_{}'.format(name),
            'VectorSpeciesReport.json'
        )

