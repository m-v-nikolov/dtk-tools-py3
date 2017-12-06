import os

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from dtk.utils.reports.CustomReport import BaseReport


# only run via 'dtk catalyst'
SetupParser.default_block = 'CATALYSTREGRESSIONHPC'

# Tell this module how to find the config and campaign files to be used. Set campaign_file to None if not used.
input_dir = os.getcwd() # path.dirname(os.path.abspath(__file__))
config_file = os.path.join(input_dir, 'config.json')
campaign_file = os.path.join(input_dir, 'campaign.json')

# since some of the tests use up-relative pathing, which is anathema to AssetManager, we need
# to copy any such referenced files to this case directory AND then update the referencing json file.


kwargs = {
}
cb = DTKConfigBuilder.from_files(config_name=config_file, campaign_name=campaign_file, **kwargs)

# Name of the experiment
# exp_name = 'catalyst_comparison-MalariaSandbox'
cwd = os.path.abspath(os.getcwd())
component2 = os.path.split(cwd)[1]
component1 = os.path.split(os.path.split(cwd)[0])[1]
exp_name = 'TestSpeedup-%s-%s' % (component1, component2)

# when run with 'dtk catalyst', run_sim_args['exp_name'] will have additional information appended.
run_sim_args =  {
    'exp_name': exp_name,
    # 'exp_builder': builder, # users may have created one; this will be overridden in 'dtk catalyst'
    'config_builder': cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
