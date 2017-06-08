import os

from dtk.generic.migration import single_roundtrip_params
from dtk.tools.spatialworkflow.SpatialManager import SpatialManager
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from simtools.SetupParser import SetupParser

location = 'HPC' #'LOCAL'
setup = SetupParser.init(location)
geography = 'DRC/Bandundu'
sites = ['Bandundu']

dll_root = SetupParser.get('dll_root')


builder   = GenericSweepBuilder.from_dict({'_site_':sites, # study sites
                                           #'x_Local_Migration':[1e-2],
                                           'Run_Number':range(1)    # random seeds
                                          })

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM',
                                    #Num_Cores=24,
                                    Num_Cores=1,
                                    Simulation_Duration=365*5)

# migration
cb.update_params(single_roundtrip_params)

# set demographics file name
cb.update_params({'Demographics_Filenames':[os.path.join(geography,"DRC_Bandundu_1_node_demographics.json")]})

# modify the config for the geography of interest
cb.update_params({'Geography': geography})

# Spatial simulation + migration settings
cb.update_params({
                # Match demographics file for constant population size (with exponential age distribution)
                'Birth_Rate_Dependence': 'FIXED_BIRTH_RATE', 
                'Enable_Nondisease_Mortality': 1, 
                'New_Diagnostic_Sensitivity': 0.025, # 40/uL
                #'Vector_Sampling_Type': 'SAMPLE_IND_VECTORS', # individual vector model (required for vector migration)
                #'Mosquito_Weight': 10,
                "Migration_Model": "NO_MIGRATION",
                #'Enable_Vector_Migration': 1, # mosquito migration
                #'Enable_Vector_Migration_Local': 1, # migration rate hard-coded in NodeVector::processEmigratingVectors() such that 50% total leave a 1km x 1km square per day (evenly distributed among the eight adjacent grid cells).
                #'Local_Migration_Filename': os.path.join(geography,'Zambia_Gwembe_Sinazongwe_115_nodes_local_migration.bin'),
                #'Enable_Local_Migration':1,
                #'Migration_Pattern': 'SINGLE_ROUND_TRIPS', # human migration
                #'Migration_Pattern': 'NO_MIGRATION', # human migration
                #'Local_Migration_Roundtrip_Duration': 2, # mean of exponential days-at-destination distribution
                #'Local_Migration_Roundtrip_Probability': 0.95, # fraction that return

                #'Enable_Spatial_Output': 1, # spatial reporting
                #'Spatial_Output_Channels': ['New_Infections','Population', 'Prevalence', 'New_Diagnostic_Prevalence', 'Daily_EIR', 'New_Clinical_Cases', 'Adult_Vectors', 'Human_Infectious_Reservoir', 'Daily_Bites_Per_Human', 'Infectious_Vectors', 'Land_Temperature','Relative_Humidity', 'Rainfall', 'Air_Temperature', 'Mean_Parasitemia']
                #'Spatial_Output_Channels': ['Population', 'Prevalence', 'New_Diagnostic_Prevalence', 'Daily_EIR', 'New_Clinical_Cases', 'Adult_Vectors', 'Human_Infectious_Reservoir', 'Daily_Bites_Per_Human']
                })

# multi-core load balance settings
#cb.update_params({'Load_Balance_Filename': os.path.join(geography,'Zambia_Gwembe_Sinazongwe_115_nodes_loadbalance_24procs.bin')})

exp_name = 'DRC_Bandundu test'

# Working directory is current dir for now
working_dir = os.path.abspath('.')
input_path = os.path.join(working_dir,"input")
output_dir = os.path.join(working_dir,"output")
population_input_file = 'pop_bandundu.csv' # see format in dtk.tools.spatialworkflow.DemographicsGenerator
migration_matrix_input_file = 'adj_list.json.' # see format in dtk.tools.migration.MigrationGenerator.process_input 
immunity_burnin_meta_file = 'immune_burnin_meta.json' # see format in dtk.tools.spatialworkflow.ImmunityOverlaysGenerator.generate_immune_overlays
nodes_params_input_file = 'nodes_params.json' # see format in dtk.tools.spatialworkflow.ImmunityOverlaysGenerator


# Create the spatial_manager
spatial_manager = SpatialManager(
                                     location,
                                     cb,
                                     geography, 
                                     exp_name, 
                                     working_dir, 
                                     input_path, 
                                     population_input_file = population_input_file, 
                                     output_dir = output_dir, 
                                     log = True, 
                                     #migration_matrix_input_file = migration_matrix_input_file, 
                                     #num_cores = 24, 
                                     num_cores = 1,
                                     #immunity_burnin_meta_file = immunity_burnin_meta_file,
                                     #nodes_params_input_file = nodes_params_input_file, 
                                     #update_demographics = fun.partial(apply_pop_scale_larval_habitats, os.path.join(input_path, nodes_params_input_file)),
                                     #generate_climate = True
                                 )

# Run!
spatial_manager.run()

run_sim_args =  {'config_builder': cb,
                 'exp_name': exp_name,
                 'exp_builder': builder}
