from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Set the default configuration block to HPC (we will run on COMPS)
SetupParser.default_block = 'HPC'

# Choose a name for our experiment
exp_name = 'Example with arbitrary local files'

# Create a default ConfigBuilder
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

# Set the collection to be the COMPS Namawala
cb.set_input_collection('Namawala')

# Configure the simulation to point to the input files of the default collection
cb.set_param('Air_Temperature_Filename','Namawala_single_node_air_temperature_daily.bin')
cb.set_param('Land_Temperature_Filename', 'Namawala_single_node_land_temperature_daily.bin')
cb.set_param('Demographics_Filenames', ['Namawala_single_node_demographics.json'])
cb.set_param('Rainfall_Filename','Namawala_single_node_rainfall_daily.bin')
cb.set_param('Relative_Humidity_Filename','Namawala_single_node_relative_humidity_daily.bin')

# Override the temperature files
# To override files in a collection, it is important to use the exact same name and relative path
# For COMPS default collections, the files are directly in the root, so relative_path is not set when adding the file
# Also we are using the exact same name: Namawala_single_node_air_temperature_daily.bin
cb.experiment_files.add_file("inputs/overrides/Namawala_single_node_air_temperature_daily.bin")
cb.experiment_files.add_file("inputs/overrides/Namawala_single_node_air_temperature_daily.bin.json")


run_sim_args = {
    'exp_name': exp_name,
    'config_builder': cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(**run_sim_args)