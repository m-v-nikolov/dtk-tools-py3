## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'
import numpy as np

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory

# Run on HPC
SetupParser.default_block = "HPC"

# Configure a default 5 years simulation
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM', Simulation_Duration=365 * 5)

# Set it in Namawala
configure_site(cb, 'Namawala')

# Name of the experiment
exp_name = 'ExampleSweep'


# Create a builder to sweep over the birth rate multiplier
builder = GenericSweepBuilder.from_dict({'x_Birth': np.arange(1, 1.5, .01)})

run_sim_args = {
    'exp_name': exp_name,
    'exp_builder': builder,
    'config_builder': cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    exp_manager.wait_for_finished(verbose=True)
    assert(exp_manager.succeeded())
