from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Set the default configuration block to HPC (we will run on COMPS)
SetupParser.default_block = 'HPC'

# Choose a name for our experiment
exp_name = 'Example with arbitrary local files'

# Create a default ConfigBuilder
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

# Add an arbitrary file in the experiment
cb.experiment_files.add_file("inputs/arbitrary_file.txt")

# ... but we can also add a folder content
# The relative path argument is used to force a relative_path in the asset collection
# everything coming from inputs/docs will then be placed inside a "docs" folder.
cb.experiment_files.add_path("inputs/docs", relative_path="docs")


run_sim_args = {
    'exp_name': exp_name,
    'config_builder': cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(**run_sim_args)