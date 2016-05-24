import os
import json
import functools as fun


from dtk.generic.migration import single_roundtrip_params
from dtk.vector.study_sites import configure_site
from simtools.SetupParser import SetupParser
from dtk.utils.core.DTKConfigBuilder import DTKConfigBuilder
from dtk.tools.spatialworkflow.SpatialManager import SpatialManager
from dtk.utils.builders.sweep import GenericSweepBuilder

'''
update demographics json based on nodes_parameters (e.g. laral habitat scales) and demographics (e.g. InitialPopulation)
'''
def apply_pop_scale_larval_habitats(nodes_params_input_file_path, demographics = None):
    
    with open(nodes_params_input_file_path, 'r') as np_f:
        nodes_params = json.load(np_f)
    
        for node_item in demographics['Nodes']:
            node_label = node_item['NodeAttributes']['FacilityName']

            arab_h = nodes_params[node_label]['arab']
            fun_h = nodes_params[node_label]['fun']
            
            calib_single_node_pop = 1000
            pop_multiplier = node_item['NodeAttributes']['InitialPopulation']/(calib_single_node_pop + 0.0)
            arab_multiplier = arab_h*pop_multiplier
            fun_multiplier = fun_h*pop_multiplier
            
          
            node_item['NodeAttributes']['LarvalHabitatMultiplier'] = {
                                                                          'TEMPORARY_RAINFALL':arab_multiplier,
                                                                          'CONSTANT':1.0*pop_multiplier,
                                                                          'WATER_VEGETATION':1.0*pop_multiplier,
                                                                          'PIECEWISE_MONTHLY':fun_multiplier
                                                                      }
        
    return demographics
    
    

setup = SetupParser()
location = 'HPC' #'LOCAL' 
geography = 'Zambia/Gwembe_Sinazongwe_115_nodes'
sites = ['Gwembe_Sinazongwe_115_nodes']

dll_root = setup.get('BINARIES', 'dll_path')


builder   = GenericSweepBuilder.from_dict({'_site_':sites, # study sites
                                           'x_Local_Migration':[1e-2],
                                           'Run_Number':range(10)    # random seeds
                                          })

cb = DTKConfigBuilder.from_defaults('MALARIA_SIM',
                                    Num_Cores=24,
                                    Simulation_Duration=365*5)

# migration
cb.update_params(single_roundtrip_params)

# demographics
cb.update_params({'Demographics_Filename':"Zambia_30arcsec_demographics.json"})

# modify the config for the geography of interest
cb.update_params({
                'Geography': geography, 
                'New_Diagnostic_Sensitivity': 0.025, # 40/uL
                'Load_Balance_Filename': 'Zambia_Gwembe_Sinazongwe_115_nodes_loadbalance_24procs.bin'
                })

# Working directory is current dir for now
working_dir = os.path.abspath('.')
input_path = os.path.join(working_dir,"input")
output_dir = os.path.join(working_dir,"output")
population_input_file = 'pop.csv' # see format in dtk.tools.spatialworkflow.DemographicsGenerator
migration_matrix_input_file = 'migration.csv' # see format in dtk.tools.migration.MigrationGenerator.process_input 
immunity_burnin_meta_file = 'immunity_meta.json' # see format in dtk.tools.spatialworkflow.ImmunityOverlaysGenerator.generate_immune_overlays
nodes_params_input_file = 'best_fit_params.json' # see format in dtk.tools.spatialworkflow.ImmunityOverlaysGenerator

# Create the spatial_manager

spatial_manager = SpatialManager(
                                     cb, 
                                     setup, 
                                     geography, 
                                     'Spatial Example', 
                                     working_dir, 
                                     input_path, 
                                     population_input_file, 
                                     output_dir = output_dir, 
                                     log = True, 
                                     migration_matrix_input_file = migration_matrix_input_file, 
                                     num_cores = 24, 
                                     immunity_burnin_meta_file = immunity_burnin_meta_file,
                                     nodes_params_input_file = nodes_params_input_file, 
                                     update_demographics = fun.partial(apply_pop_scale_larval_habitats, os.path.join(input_path, nodes_params_input_file))
                                 )
 

# Run!
spatial_manager.run()