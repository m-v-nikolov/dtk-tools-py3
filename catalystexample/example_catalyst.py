## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'
import numpy as np
import os

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

# Run on HPC
SetupParser.default_block = "HPC"

# Configure a default 5 years simulation
# sim_duration = None if exp_def['duration'] is None or exp_def['duration'] == 'all' else int(exp_def['duration']) # ck4, pasted

# Tell this module how to find the config and campaign files to be used. Set campaign_file to None if not used.
input_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "input")
config_file = os.path.join(input_dir, 'config.json')
campaign_file = os.path.join(input_dir, 'campaign.json')
kwargs = { # ck4, need any kwargs for catalyst test script?
    # 'Simulation_Duration': sim_duration
}
cb = DTKConfigBuilder.from_files(config_name=config_file, campaign_name=campaign_file, **kwargs)

# ck4, may be entirely unnecessary OR entirely rewritten for catalyst
# configure_site(cb,'Namawala') # ck4 edit; read from some config or hard code, depending on the exact config

# Name of the experiment
# exp_name  = 'ExampleSweep' # ck4, read from some config? duplicate fidelity_report somehow:

# ck4, block pasted
# Case name is used as an experiment name. Experiment name is then used as a prefix of the output dir (set in the analyzer).
exp_name = 'example_catalyst-MalariaSandbox' #'{}-{}_{}'.format(args.case_name or case_name_default, args.build_label, exp_def['def_name'])
exp_name = exp_name.replace('-_', '_')

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
