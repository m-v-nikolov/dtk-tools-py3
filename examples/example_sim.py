from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# For example only -- Force the selected block to be EXAMPLE
SetupParser("EXAMPLE")

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

run_sim_args =  {'config_builder': cb,
                 'exp_name': 'ExampleSim'}


if __name__ == "__main__":
    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.create_simulations(**run_sim_args)
    # exp_manager.run_simulations(**run_sim_args)