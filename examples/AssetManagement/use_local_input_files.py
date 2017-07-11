from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Set the default configuration block to HPC (we will run on COMPS)
SetupParser.default_block = 'LOCAL'

# Choose a name for our experiment
exp_name = 'Example with custom set of input files'

# Create a default ConfigBuilder
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

# Configure the simulation to point to our input files
cb.set_param('Air_Temperature_Filename','Namawala_temperature.bin')
cb.set_param('Land_Temperature_Filename', 'Namawala_temperature.bin')
cb.set_param('Demographics_Filenames', ['Namawala_demog.json'])
cb.set_param('Rainfall_Filename','Namawala_rainfall.bin')
cb.set_param('Relative_Humidity_Filename','Namawala_humidity.bin')

# Point to the folder containing the local files
# We can either set it through the code as shown below, or in the simtools.ini by setting:
# - base_collection_id_input  =
# - input_root = absolute_path_to/inputs/Namawala
cb.set_input_files_root('inputs/Namawala')

run_sim_args = {
    'exp_name': exp_name,
    'config_builder': cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(**run_sim_args)