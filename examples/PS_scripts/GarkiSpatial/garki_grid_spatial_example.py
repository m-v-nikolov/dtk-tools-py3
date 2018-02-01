import os
import json
import functools as fun
import itertools as it

from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModFn, ModBuilder



from dtk.generic.migration import single_roundtrip_params
from dtk.vector.study_sites import configure_site
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.tools.spatialworkflow.SpatialManager import SpatialManager
from dtk.utils.builders.sweep import GenericSweepBuilder
from dtk.vector.species import set_larval_habitat
from dtk.interventions.outbreakindividual import recurring_outbreak
from dtk.interventions.health_seeking import add_health_seeking
from dtk.interventions.heg import heg_release
from dtk.utils.reports.VectorReport import add_human_migration_report
# from dtk.utils.reports.VectorReport import add_vector_migration_report
from simtools.SetupParser import SetupParser


def apply_pop_scale_larval_habitats(nodes_params_input_file_path, demographics):
    
    with open(nodes_params_input_file_path, 'r') as np_f:
        nodes_params = json.load(np_f)
    
    for node_item in demographics['Nodes']:
        node_label = node_item['NodeAttributes']['FacilityName']

        const_h = nodes_params[node_label]['const_h']
        temp_h = nodes_params[node_label]['temp_h']
    
        calib_single_node_pop = 1000 # change if needed
        #node_item['NodeAttributes']['InitialPopulation'] = 7500
        
        #node_item['NodeAttributes']['InitialPopulation'] = max(node_item['NodeAttributes']['InitialPopulation'], 400)
        
        birth_rate = (float(node_item['NodeAttributes']['InitialPopulation'])/(1000 + 0.0))*0.12329
        node_item['NodeAttributes']['BirthRate'] = birth_rate
        pop_multiplier = float(node_item['NodeAttributes']['InitialPopulation'])/(calib_single_node_pop + 0.0)
        #pop_multiplier = 1
        const_multiplier = const_h*pop_multiplier
        temp_multiplier = temp_h*pop_multiplier
            
        #node_item['NodeAttributes']['InitialPopulation'] = 500
        node_item['NodeAttributes']['LarvalHabitatMultiplier'] = {
                                                                          'TEMPORARY_RAINFALL':temp_multiplier,
                                                                          'LINEAR_SPLINE':const_multiplier,
                                                                      }

    return demographics


location = 'HPC' #'LOCAL'
setup = SetupParser(location)
geography = 'Garki\\Garki_gridded_net' # notice geography matches one of the haiti geographies in the dict geographies of dtk/generic/geography.py
site = 'Garki_gridded_net' # notice site matches (all lower case) one of the study sites (i.e. configure_haiti_gridded_households) in dtk/vector/study_sites.py

prefix = "GarkiNE"

exp_name = prefix + "_pop_rep_3_locations_con_sw_w_seasonality"

num_cores = 24

num_years = 1


builder = ModBuilder.from_combos(
                                    [ModFn(configure_site, site)],
                                    [ModFn(DTKConfigBuilder.set_param, "x_Vector_Migration_Local", vm) for vm in [1]],#, 5*1e-1, 1]],
                                    [ModFn(DTKConfigBuilder.set_param, 'Run_Number', r) for r in range(1,2)],
                                    
                                    # [ModFn(DTKConfigBuilder.set_param, 'HEG_Infection_Modification', im) for im in [0.05]],
                                    # [ModFn(DTKConfigBuilder.set_param, 'HEG_Fecundity_Limiting', fl) for fl in [0.05]],
                                    # [ModFn(DTKConfigBuilder.set_param, 'HEG_Homing_Rate', hr) for hr in [0.95]],
                                    # [ModFn(heg_release, num_released, num_repetitions = 10, released_species = "arabiensis", start_day = d, node_list = range(200, 300, 45)) for (num_released, d)  in [(500, 480)]],
                                    #[ModFn(heg_release, num_released, num_repetitions = 52, released_species = "arabiensis", start_day = d, node_list = [1]) for (num_released, d)  in [(500, 365)]],
                                    #[ModFn(heg_release, num_released, num_repetitions = 52, released_species = "arabiensis", start_day = d, node_list = range(1, 400, 20)) for (num_released, d)  in [(500, 365)]],
                                )


cb = DTKConfigBuilder.from_defaults('VECTOR_SIM',
                                    Num_Cores=num_cores,
                                    Simulation_Duration=int(365*num_years))


# set demographics file name
cb.update_params({'Demographics_Filenames':[os.path.join(geography, prefix + "_demographics.json")]})

# modify the config for the geography of interest
cb.update_params({'Geography': geography})

cb.update_params({'Vector_Species_Names':['gambiae']})

# Spatial simulation + migration settings
cb.update_params({
                # Match demographics file for constant population size (with exponential age distribution)
                'Birth_Rate_Dependence': 'FIXED_BIRTH_RATE', 
                'Enable_Nondisease_Mortality': 1, 
                'New_Diagnostic_Sensitivity': 0.025, # 40/uL
                'Vector_Sampling_Type': "VECTOR_COMPARTMENTS_NUMBER",
                "Roundtrip_Waypoints": 5,
                #'Mosquito_Weight': 10,
                'Enable_Vector_Migration': 1, # mosquito migration
                'Enable_Vector_Migration_Local': 1,
                 
                "Vector_Migration_Filename_Local":os.path.join(geography, prefix + '_vector_migration.bin'),
                'Local_Migration_Filename': os.path.join(geography, prefix + '_migration.bin'), # note that underscore prior 'migration.bin' is required for legacy reasons that need to be refactored...
                'Enable_Local_Migration':0,
                #'Migration_Pattern': 'SINGLE_ROUND_TRIPS', # human migration
                #'Local_Migration_Roundtrip_Duration': 2, # mean of exponential days-at-destination distribution
                #'Local_Migration_Roundtrip_Probability': 0.95, # fraction that return
                'Migration_Model': 'NO_MIGRATION', # human migration
                'Enable_Spatial_Output': 1, # spatial reporting
                'Spatial_Output_Channels': ["Adult_Vectors", 'Infectious_Vectors', 'New_Infections', 'Population', 'Prevalence', 'Daily_Bites_Per_Human', 'Land_Temperature','Relative_Humidity', 'Rainfall', 'Air_Temperature']
                })


cb.update_params({"Default_Geography_Initial_Node_Population": 1000,
                  "Default_Geography_Torus_Size": 10,
                  "Enable_Vector_Migration_Human": 0,
                  "Enable_Vector_Migration_Wind": 0,
                  "Egg_Hatch_Density_Dependence":"NO_DENSITY_DEPENDENCE",
                  "Temperature_Dependent_Feeding_Cycle": "NO_TEMPERATURE_DEPENDENCE",
                  "Enable_Drought_Egg_Hatch_Delay": 0,
                  "Enable_Egg_Mortality": 0,
                  "Enable_Temperature_Dependent_Egg_Hatching": 0,
                  "Vector_Migration_Modifier_Equation": "LINEAR"
                  })


#cb.update_params({'Climate_Model':'CLIMATE_CONSTANT'})

cb.set_param("Enable_Demographics_Builtin", 0)
cb.set_param("Valid_Intervention_States", [])
#cb.set_param("Enable_Memory_Logging", 1)

# HEG parameters
# cb.update_params({
#                   'HEG_Model':'DUAL_GERMLINE_HOMING',
#                   #'HEG_Model':'DRIVING_Y',
#                   });
                  

# mosquito parameters
cb.update_params({
                  "Larval_Density_Dependence": "NO_DENSITY_DEPENDENCE",
                  "Age_Dependent_Biting_Risk_Type": "OFF",
                  "Larval_Density_Mortality_Scalar":1.0,
                  "Larval_Density_Mortality_Offset": 0.001,
                  })

# multi-core load balance settings
cb.update_params({'Load_Balance_Filename': os.path.join(geography, prefix + '_loadbalance_' +str(num_cores) + 'procs.bin')})
#recurring_outbreak(cb, outbreak_fraction = 0.01, tsteps_btwn=180)
#recurring_outbreak(cb, outbreak_fraction = 0.005, tsteps_btwn=180)



'''
# track migration of people (this can generate really big files by default use with care
cb.update_params({
                  "Report_Event_Recorder": 1,
                  "Listed_Events": ["Immigrating", "Emigrating"],
                  "Report_Event_Recorder_Events":["Immigrating", "Emigrating"],
                  "Report_Event_Recorder_Ignore_Events_In_List" : 0
                  })
'''


'''
# various log levels allowing different levels of output verbsity per class
# to reduce output (and stdout sise) escalate debug level over DEBUG, INFO, WARNING, and ERROR (error resulting in the least output)
# use LogLevel_Memory set to DEBUG to see simulation memory footprint on each core (CPU)


cb.update_params({
                    "logLevel_VectorHabitat": "ERROR",
                    "logLevel_NodeVector": "ERROR",
                    "logLevel_JsonConfigurable": "ERROR",

                    "logLevel_MosquitoRelease": "ERROR",
                    "logLevel_VectorPopulationIndividual": "ERROR",

                    "logLevel_NodeEventContext": "WARNING",  # UnregisterIndividualEventObserver
                    "logLevel_SimulationEventContext": "ERROR",  # Discarding old event for t=...
                    "logLevel_NodeLevelHealthTriggeredIV": "WARNING",  # NLHTI is listenting to ... events
                    "logLevel_StandardEventCoordinator": "WARNING",  # UpdateNodes distributed ... intervention to ...

                    "logLevel_SimulationEventContext": "WARNING",
                    "logLevel_JsonConfigurable": "WARNING",
                    "logLevel_NodeLevelHealthTriggeredIV": "WARNING",
                    "logLevel_Memory": "DEBUG"
                  })
'''

# Working directory is current dir for now
# working_dir = os.path.abspath('.')
working_dir = 'Q:\Malaria\pselvaraj\Simulations\data_inputs'
input_path = os.path.join(working_dir,"input")
output_dir = os.path.join(working_dir,"output")
population_input_file = 'garki_NE_pop_grid100m_cluster_labels.csv' # see format in dtk.tools.spatialworkflow.DemographicsGenerator
nodes_params_input_file = "garki_grid_net_habs.json"
#migration_matrix_input_file = "gridded_households_adj_list.json"


# Create the spatial_manager
spatial_manager = SpatialManager(
                                     location,
                                     cb,
                                     geography,
                                     exp_name,
                                     working_dir, 
                                     input_path, 
                                     sim_data_input_root = 'Q:\Malaria\pselvaraj\Simulations\data_inputs', # assuming the input files will reside on COMPS user's directory (e.g. \\idmppfil01\idm\home\user_name) which is mapped to T as a network drive; change if necessary
                                     population_input_file=population_input_file,
                                     update_demographics = fun.partial(apply_pop_scale_larval_habitats, os.path.join(input_path, nodes_params_input_file)),
                                     #migration_matrix_input_file = migration_matrix_input_file,  
                                     output_dir = output_dir, 
                                     log = False,
                                     num_cores = num_cores, 
                                     
                                     generate_climate = False,
                                     generate_migration = False,
                                     generate_load_balancing = False,
                                     generate_immune_overlays = False,
                                     existing_demographics_file_path=None
                                 )


# add_vector_migration_report(cb)

# set demographics parameters
spatial_manager.set_demographics_type("static")
spatial_manager.set_resolution("custom")
#spatial_manager.set_climate_project_info("IDM-Zambia")
#spatial_manager.set_climate_start_year("2014")
#spatial_manager.set_climate_num_years("1")

# spatial_manager.set_graph_topo_type("custom")
# spatial_manager.set_link_rates_model_type("custom")
#
#
# with open(os.path.join(working_dir, "input", "garki_vector_migration_rates.json"), "r") as g_f:
#     link_rates = json.load(g_f)
#
# spatial_manager.set_link_rates(link_rates)

spatial_manager.run()

run_sim_args = {'config_builder': cb,
                 'exp_name': exp_name,
                 'exp_builder': builder}

SetupParser.default_block = 'HPC'

if __name__ == "__main__":
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**run_sim_args)
    # Wait for the simulations to be done
    exp_manager.wait_for_finished(verbose=True)
    assert (exp_manager.succeeded())
