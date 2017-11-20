import os

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

# Run on HPC
SetupParser.default_block = "HPC"

# Tell this module how to find the config and campaign files to be used. Set campaign_file to None if not used.
input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
config_file = os.path.join(input_dir, 'config.json')
campaign_file = os.path.join(input_dir, 'campaign.json')

kwargs = {
}
cb = DTKConfigBuilder.from_files(config_name=config_file, campaign_name=campaign_file, **kwargs)

# Name of the experiment
exp_name = 'catalyst_comparison-WAPertussis'

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
