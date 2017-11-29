from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
SetupParser.default_block = 'HPC'

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM', Simulation_Duration=3650)
configure_site(cb, 'Namawala')

# run_sim_args is what the `dtk run` command will look for
run_sim_args = {
    'exp_name': 'ExampleSim',
    'config_builder': cb
}

# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
