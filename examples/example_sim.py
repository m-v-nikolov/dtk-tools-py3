from COMPS.Data import Experiment, QueryCriteria

from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.AnalyzeManager.AnalyzeHelper import consolidate_experiments_with_options, list_batch
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# This block will be used unless overridden on the command-line
from simtools.Utilities.COMPSUtilities import COMPS_login, get_experiment_ids_for_user
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation

SetupParser.default_block = 'LOCAL'

cb = DTKConfigBuilder.from_defaults('VECTOR_SIM',Simulation_Duration=10000)
configure_site(cb, 'Namawala')

# run_sim_args is what the `dtk run` command will look for
run_sim_args =  {
    'exp_name': 'ExampleSim',
    'config_builder': cb
}

# If you prefer running with `python example_sim.py`, you will need the following block
if __name__ == "__main__":
    # SetupParser.init()
    # exp_manager = ExperimentManagerFactory.init()
    # exp_manager.run_simulations(**run_sim_args)
    # # Wait for the simulations to be done
    # exp_manager.wait_for_finished(verbose=True)
    # assert(exp_manager.succeeded())

    COMPS_login('https://comps2.idmod.org')
    print(get_experiment_ids_for_user('braybaud'))



    # print(DataStore.delete_experiment(retrieve_experiment('13948fa4-81b3-e711-80c3-f0921c167860')))