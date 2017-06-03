from dtk.utils.analyzers import TimeseriesAnalyzer
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
from simtools.Utilities.Experiments import retrieve_experiment

SetupParser.default_block = 'EXAMPLE'

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

run_sim_args =  {
    'config_builder': cb,
    'exp_name': 'ExampleSim',
}

if __name__ == "__main__":
    exp_manager = ExperimentManagerFactory.from_setup()
    exp_manager.run_simulations(**run_sim_args)