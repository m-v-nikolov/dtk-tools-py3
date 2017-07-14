from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.vector.study_sites import configure_site
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Set the default configuration block to HPC (we will run on COMPS)
SetupParser.default_block = 'HPC'

# Choose a name for our experiment
exp_name = 'Example with collection ID'

# Create a default ConfigBuilder
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')
configure_site(cb, 'Namawala')

# Use a given collection_id for this experiment
# see at: https://comps.idmod.org/#explore/AssetCollections?filters=Id=0001c635-ba65-e711-9401-f0921c16849d&mode=list&orderby=DateCreated+desc&count=10&offset=0&selectedId=0001c635-ba65-e711-9401-f0921c16849d
# By setting a collection_id in the config builder, this collection will be used like if we specified it for INPUT, DLL and EXE
# Therefore it is important to make sure the collection includes all necessary files
# If not, you will need to add missing files to the cb.experiment_files in order to create a new collection
cb.set_collection_id('0001c635-ba65-e711-9401-f0921c16849d')

run_sim_args = {
    'exp_name': exp_name,
    'config_builder':cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(**run_sim_args)
