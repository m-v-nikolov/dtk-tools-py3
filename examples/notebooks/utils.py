import os
import site
import ConfigParser
import imp
import pandas as pd


def write_dtk_config(max_sims, sim_root, input_root, bin_path, exe_path):
    conf_path = os.path.join(site.getsitepackages()[1], 'dtk', 'dtk_setup.cfg')
    print conf_path
    config = ConfigParser.RawConfigParser()
    config.read(conf_path)

    config.set('LOCAL', 'max_local_sims', max_sims)
    config.set('LOCAL', 'sim_root', sim_root)
    config.set('LOCAL', 'input_root', input_root)
    config.set('LOCAL', 'bin_root', bin_path)
    config.set('BINARIES', 'exe_path', exe_path)

    with open(conf_path, 'wb') as configfile:
        config.write(configfile)
    
    #make sure the simulations dir exists
    if not os.path.exists(sim_root):
        os.mkdir(sim_root)

    print "The dtk_config.cfg file has been successfully updated!"


def test_if_dtk_present():
    try:
        imp.find_module('dtk')
        print "The DTK module is present and working!"
    except ImportError:
        print "The DTK module is not present... Make sure it is properly installed and imported!"


def test_if_simulation_done(states):
    if states.values()[0] == "Finished":
        print "The simulation completed successfully!"
    else:
        print "A problem has been encountered. Please try to run the code block again."




class NotebookAnalyzer():

    data_group_names = ['group', 'sim_id', 'channel']
    ordered_levels = ['channel', 'group', 'sim_id']

    def __init__(self,
                 filename = 'InsetChart.json',
                 filter_function = lambda md: True, # no filtering based on metadata
                 select_function = lambda ts: pd.Series(ts), # return complete-&-unaltered timeseries
                 group_function  = lambda k,v: k, # group by unique simid-key from parser
                 channels = [ 'Statistical Population',
                              'Rainfall', 'Adult Vectors',
                              'Daily EIR', 'Infected']):

        self.filenames = [filename]
        self.channels = channels
        self.group_function = group_function
        self.filter_function = filter_function
        self.select_function = select_function

    def filter(self, sim_metadata):
        return self.filter_function(sim_metadata)

    def validate_channels(self, keys):
        self.channels = [c for c in self.channels if c in keys] if self.channels else keys

    def get_channel_data(self, data_by_channel, header=None):
        channel_series = [self.select_function(data_by_channel[channel]["Data"]) for channel in self.channels]
        return pd.concat(channel_series, axis=1, keys=self.channels)

    def apply(self, parser):
        data = parser.raw_data[self.filenames[0]]
        data_by_channel = data['Channels']
        self.validate_channels(data_by_channel.keys())
        channel_data = self.get_channel_data(data_by_channel, data['Header'])
        channel_data.group = self.group_function(parser.sim_id, parser.sim_data)
        channel_data.sim_id = parser.sim_id
        return channel_data

    def combine(self, parsers):
        selected = [p.selected_data[id(self)] for p in parsers.values() if id(self) in p.selected_data]
        combined = pd.concat(selected, axis=1,
                             keys=[(d.group, d.sim_id) for d in selected],
                             names=self.data_group_names)
        self.data = combined.reorder_levels(self.ordered_levels, axis=1).sortlevel(axis=1)

    def finalize(self):
        ax = self.data.plot(legend=True, subplots=True)
        i = 0
        for plot in ax:
            plot.legend((self.channels[i],),loc="best")
            i+=1
