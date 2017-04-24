## Execute directly: 'python example_sweep.py'
## or via the dtk.py script: 'dtk run example_sweep.py'
import numpy as np

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.study_sites import configure_site
from simtools.SetupParser import SetupParser

# For example only -- Force the selected block to be EXAMPLE
sp = SetupParser("EXAMPLE")

# Configure a default 5 years simulation
cb = DTKConfigBuilder.from_defaults('MALARIA_SIM',
                                    Simulation_Duration=365*5)
# Set it in Namawala
configure_site(cb,'Namawala')

# Name of the experiment
exp_name  = 'ExampleSweep'

# Create a builder to sweep over the birth rate multiplier
builder = GenericSweepBuilder.from_dict({'x_Birth': np.arange(1,1.5,.1)})


run_sim_args =  {'config_builder': cb,
                 'exp_name': exp_name,
                 'exp_builder': builder}


if __name__ == "__main__":
    from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)
