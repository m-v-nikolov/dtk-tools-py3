from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Set the default configuration block to HPC (we will run on COMPS)
SetupParser.default_block = 'HPC'

# Choose a name for our experiment
exp_name = 'Example with custom executable'

# Create a default ConfigBuilder
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

# Create a basic sweep
builder = GenericSweepBuilder.from_dict({'Run_Number': range(3)})

# Set the executable we will use
# We can either set it through the code as shown below, or in the simtools.ini by setting:
# - base_collection_id_exe  =
# - exe_path = absolute_path_to/inputs/Custom_eradication.exe
cb.set_experiment_executable('inputs/Custom_eradication.exe')

run_sim_args = {
    'exp_name': exp_name,
    'exp_builder': builder,
    'config_builder':cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(**run_sim_args)
