from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

# Set the default configuration block to HPC (we will run on COMPS)
SetupParser.default_block = 'HPC'

# Choose a name for our experiment
exp_name = 'Example with COMPS default collections'

# Create a default ConfigBuilder
cb = DTKConfigBuilder.from_defaults('VECTOR_SIM')

# Set the default collection to be the system Namawala
# see at: https://comps.idmod.org/#explore/AssetCollections?mode=list&orderby=DateCreated+desc&count=10&offset=10&layout=502C50&selectedId=e7506212-915b-e711-9401-f0921c16849d
# The default collections supports either a Name or an ID.
cb.set_input_collection('Namawala')

# Configure the simulation to point to the input files of the default collection
cb.set_param('Air_Temperature_Filename','Namawala_single_node_air_temperature_daily.bin')
cb.set_param('Land_Temperature_Filename', 'Namawala_single_node_land_temperature_daily.bin')
cb.set_param('Demographics_Filenames', ['Namawala_single_node_demographics.json'])
cb.set_param('Rainfall_Filename','Namawala_single_node_rainfall_daily.bin')
cb.set_param('Relative_Humidity_Filename','Namawala_single_node_relative_humidity_daily.bin')

# Use the default EMOD 2.10
# see at: https://comps.idmod.org/#explore/AssetCollections?mode=list&orderby=DateCreated+desc&count=10&offset=20&selectedId=f1f81958-925b-e711-9401-f0921c16849d
cb.set_exe_collection("EMOD 2.10")

run_sim_args = {
    'exp_name': exp_name,
    'config_builder': cb
}

if __name__ == "__main__":
    SetupParser.init()
    exp_manager = ExperimentManagerFactory.from_cb(cb)
    exp_manager.run_simulations(**run_sim_args)