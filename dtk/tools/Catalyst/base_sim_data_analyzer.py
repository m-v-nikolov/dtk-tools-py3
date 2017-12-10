import os
from collections import defaultdict

import numpy as np
import pandas as pd

from dtk.utils.analyzers.BaseAnalyzer import BaseAnalyzer


class BaseSimDataAnalyzer(BaseAnalyzer):
    """Collect simulation data into SimData objects, one for each simulation."""
    def __init__(self, output_path, config_file, demographics_file, spatial_channel_names=[], inset_channel_names=[], label=None):
        self.config_file = config_file
        self.spatial_channel_names = spatial_channel_names
        self.inset_channel_names = inset_channel_names
        self.label = label
        self.output_path = output_path

        # setup parameters for output file download
        self.filenames = ['status.txt']
        if config_file:
            self.filenames.append(config_file)
        else:
            raise Exception('A config filename must be provided.')

        # These are currently only accessible via AssetManager
        if demographics_file:
            self.demographics_file = "Assets\\" + demographics_file
            self.filenames.append(self.demographics_file)
        else:
            raise Exception('A demographics filename must be provided.')

        self.filenames.extend(self.spatial_channel_files)

        if self.inset_channel_names:
            self.filenames.append(os.path.join('output', 'InsetChart.json'))

        self.filenames = [os.path.normpath(f) for f in self.filenames]

        # init superclass now that filenames are assembled
        super(BaseSimDataAnalyzer, self).__init__()

        self.sim_data = defaultdict(SimData)
        self.result = None

    @property
    def spatial_channel_files(self):
        return [os.path.join('output', 'SpatialReport_{}.bin').format(c) for c in self.spatial_channel_names]

    def initialize(self):
        # Create the output path
        if not os.path.exists(self.output_path):
            os.makedirs(self.output_path)

    def apply(self, parser):
        # Retrieve the output directory
        sim_id = parser.sim_id

        sd = SimData()
        sd.sim_id = sim_id

        # input
        # Read the demographics
        sd.demog = DemographicsFile(data=parser.raw_data[self.demographics_file])

        # Read the config.json
        sd.config = parser.raw_data[self.config_file]["parameters"]

        # Read the status.txt
        status = parser.raw_data["status.txt"]

        # Process status
        done_str = status.strip().split("\n")[-1]
        if 'Done' not in done_str:
            raise Exception('Unable to parse run time from status.txt')
        else:
            import datetime
            h, m, s = (int(v) for v in done_str[6:].strip().split(':'))
            sd.sim_run_time = datetime.timedelta(hours=h, minutes=m, seconds=s)

        # Take care of spatial channels
        spatial = {}
        for name in self.spatial_channel_names:
            spatial[name] = SpatialChannel(parser.raw_data[name], name)
        sd.spatial_channels = spatial

        # Then take care of the InsetChart channels
        inset = {}
        ic_data = parser.raw_data["output\\InsetChart.json"]
        for name in self.inset_channel_names:
            inset[name] = InsetChannel(ic_data["Channels"][name]["Data"], name)
        sd.inset_channels = inset

        self.sim_data[sim_id] = sd

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
        if self.exp_name is None or self.exp_id is None:
            raise Exception('Experiment failed or missing. Cannot construct experiment dir path.')

        # make the reporting directory if it doesn't exist + write out some experiment metadata
        exp_path = os.path.join(self.output_path, 'catalyst_report')
        if not os.path.isdir(exp_path):
            os.makedirs(exp_path)
        return exp_path

    def get_result_path(self, name):
        rpt_path = os.path.join(self.exp_path, name)
        return rpt_path

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
        # input
        self.demog = None
        self.config = None

        # output
        self.sim_run_time = None

        self.serialized_files = None
        self.spatial_channels = None
        self.inset_channels = None


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

    def to_df(self, config_params = []):
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


class DemographicsFile:
    def __init__(self, data):
        self.json = data
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


class BaseSimDataChannel(object):
    def __init__(self, data, name, column_name, file_name):
        self.data = data
        self.name = name
        self.column_name = column_name
        self.file_name = os.path.join('output', file_name)

    @staticmethod
    def steps_series(step_count):
        steps = range(step_count)
        df = pd.DataFrame({'step': steps})

        return df


class SpatialChannel(BaseSimDataChannel):
    def __init__(self, data, name):
        super(SpatialChannel, self).__init__(data, name, SpatialChannel.spatial_column(name), 'SpatialReport_{}.bin'.format(name))

    # BaseSimDataChannel methods

    @property
    def step_count(self):
        return self.data['n_tstep']

    @property
    def values_series(self):
        row_count = self.step_count * self.node_count
        values = self.data['data']
        values = values.reshape(row_count)

        return pd.Series(values)

    def to_df(self):
        df = self.step_node_df
        df[self.column_name] = self.values_series

        return df

    @property
    def node_count(self):
        return self.data['n_nodes']

    @property
    def node_ids(self):
        return list(self.data['nodeids'])

    def node_value(self, step, node_id):
        n = self.node_ids.index(node_id)
        return self.data['data'][step][n]

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
    def __init__(self, data, name, column_name, file_name):
        super(JsonChannel, self).__init__(data, name, column_name, file_name)

    # BaseSimDataChannel methods
    @property
    def step_count(self):
        return len(self.data)

    @property
    def values_series(self):
        return pd.Series(self.data)

    def to_df(self):
        df = BaseSimDataChannel.steps_series(self.step_count)
        df[self.column_name] = self.values_series

        return df


class InsetChannel(JsonChannel):
    def __init__(self, data, name):
        super(InsetChannel, self).__init__(
            data,
            name,
            'inset_{}'.format(name),
            'InsetChart.json'
        )


class VectorSpeciesChannel(JsonChannel):
    def __init__(self, data, name):
        super(VectorSpeciesChannel, self).__init__(
            data,
            name,
            'vector_species_{}'.format(name),
            'VectorSpeciesReport.json'
        )

