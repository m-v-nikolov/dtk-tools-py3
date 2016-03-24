import os
import json
import shutil

from dtk.tools.loadbalance.LoadBalanceGenerator import LoadBalanceGenerator
from dtk.tools.migration.MigrationGenerator import MigrationGenerator
from dtk.utils.ioformat.OutputMessage import OutputMessage as om

from ImmunityOverlaysGenerator import ImmunityOverlaysGenerator
from DemographicsGenerator import DemographicsGenerator


class SpatialManager():
    '''
    Manages the creation of spatial input files..
    '''

    def __init__(self, location, cb, setup, geography, name, working_dir, input_dir, 
                 population_input_file = None,\
                 output_dir='output',\
                 log=True,\
                 num_cores = 1,\
                 migration_matrix_input_file=None,\
                 immunity_burnin_meta_file=None,\
                 nodes_params_input_file = None,\
                 update_demographics = None,\
                 existing_migration_file_path = None,\
                 existing_load_balancing_file_path = None,\
                 existing_demographics_file_path = None,\
                 existing_immunity_files_paths = None\
                 ):
        """
        Initialize the SpatialManager
        :param location: specify whether to run locally or remotely (valid options are 'LOCAL' or 'HPC' for now)
        :param name: Name of the spatial simulation.
        :param working_dir: Working directory where all inputs/outputs will be stored.
        :param input_dir: Path of the directory containing all files
        :param output_dir: Output directory name relative to working_dir
        :param log: If true, keep the intermediate files in working_dir\logs
        :param population_file: name of the population file in the inputs
        :param migration_matrix_file: name of the migration matrix file in the inputs
        :param best_fits_file: name of the best fits file in the inputs
        :param immunity_burnin_meta_file: name of the immunity file in the inputs
        :param nodes_params_input_file: contains parameter value pairs for each node (e.g. from calibration); see ImmunityOverlaysGenerator for format
        :return:
        """

        self.name = name
        self.working_dir = working_dir
        self.log = log
        self.cb = cb
        self.location = location
        
        # Set the paths
        self.current_path = os.path.join(self.working_dir, self.name)
        self.output_path = os.path.join(self.current_path,output_dir)
        self.log_path = os.path.join(self.current_path,"logs")
        self.input_path = input_dir
        
        # get local or hpc simulation data input directories from setup (i.e. dtk_setup.cfg)
        # depending o nuser input (e.g. self.location)
        # the generated demographics, migration, etc. files will be placed there
        # todo: need to add checks if these are existing directories and if not attempt to create them 
        # e.g.  some users may not have access to a remote cluster and need to set up the files locally only'
        self.sim_data_input = None
        
        
        # todo: need to modularize the local/remote test; used in other parts of the code
        if self.location == 'HPC':
            self.sim_data_input = os.path.join(setup.get('HPC', 'input_root'))
        elif self.location == 'LOCAL':
            self.sim_data_input = os.path.join(setup.get('LOCAL', 'input_root')) 
        else:
            raise ValueError(self.location + ' is not supported; select LOCAL or HPC.')
        
        
        if not existing_demographics_file_path and not population_input_file:
            raise ValueError('Valid demographics file input is required! Provide either a valid DTK demographics JSON file or a valid demographics csv file (see class DemographicsGenerator documentation for format).')
            
        
        self.existing_migration_file_path = existing_migration_file_path
        self.existing_load_balancing_file_path = existing_load_balancing_file_path
        self.existing_demographics_file_path = existing_demographics_file_path
        self.existing_immunity_files_paths = existing_immunity_files_paths

        if not existing_demographics_file_path:
            self.population_input_file_path = os.path.join(self.input_path, population_input_file)
        
        if not existing_migration_file_path and migration_matrix_input_file:
            self.migration_matrix_file_path = os.path.join(self.input_path, migration_matrix_input_file)
        else: 
            self.migration_matrix_file_path = None
            
            
        if nodes_params_input_file:
            self.nodes_params_input_file_path = os.path.join(self.input_path, nodes_params_input_file)
        else:
            self.nodes_params_input_file_path = None
            
            
        if not existing_immunity_files_paths and immunity_burnin_meta_file:
            self.immunity_burnin_meta_file_path = os.path.join(self.input_path, immunity_burnin_meta_file)
        else:
            self.immunity_burnin_meta_file_path = None
        
        
        # a user defined function automatically called with input the demographics file generaeted as part of the 
        # spatial manager workflow; the function updates demographics parameters as needed before the final demographics file is saved or used
        self.update_demographics = update_demographics
            
        # simulation number of cores (e.g. for load balancing purposes)
        self.num_cores = num_cores
        self.geography = geography


    def run(self):
        # Verify that our inputs exists
        if (not os.path.exists(self.input_path)):
            raise Exception('The input path does not exist! (%s)' % self.input_path)

        # Create the directories (output, logs, etc)
        self.create_dirs()
        
        
        # generate demographics file if it doesn't exist
        demographics = None
        
        if not self.existing_demographics_file_path:
            
            om("generating demographics file...", style = 'bold')
            
            dg = DemographicsGenerator(
                                        self.cb, 
                                        self.population_input_file_path, 
                                        demographics_type = 'static',
                                        update_demographics = self.update_demographics
                                        )
            
            demographics = dg.generate_demographics()
            
            
        else: # if existing file is provided load its content
            om("loading existing demographics file...", style = 'bold')
            om("Existing demographics file: " + self.existing_demographics_file_path)
            with open(self.existing_demographics_file_path, 'r') as demo_f:
                demographics = json.load(demo_f)
            om("Successfully loaded.")
            
        
        demog_filenames = self.cb.get_param('Demographics_Filenames')
        
        if len(demog_filenames) != 1:
            raise Exception('Expecting only one demographics filename.')
        demographics_output_file = demog_filenames[0]
        
        demographics_output_file_path = os.path.join(self.sim_data_input, demographics_output_file)
        
        with open(demographics_output_file_path,'w') as demo_f:
            json.dump(demographics, demo_f, indent = 4)
        
        om("Demographics file saved to " + demographics_output_file_path)
        
        om("", style = 'bold')

        # generate loadbalancing if load balance file is not provided;
        if not self.existing_load_balancing_file_path:
            
            om("generating cluster cores load balance file...", style = 'bold')
            
            # instantiate a load balancer; default is kmeans
            lb = LoadBalanceGenerator(self.num_cores, os.path.join(self.sim_data_input, demographics_output_file))
            
            # generate load balance across the num_cores
            lb.generate_load_balance()
            
            # save load balance binary to remote/local directory
            load_balance_filename = self.cb.get_param('Load_Balance_Filename')
            lb.save_load_balance_binary_file(os.path.join(self.sim_data_input, load_balance_filename))
            
            om("Load balance file saved to " + os.path.join(self.sim_data_input, load_balance_filename))
            
        else: # if existing file is provided copy it to the reight location
            om("Looking for existing cluster load balance file...", style = 'bold')
            
            shutil.copy(self.existing_load_balancing_file_path, os.path.join(self.sim_data_input, load_balance_filename))
            
            om("Existing cluster cores load balance file found at: " + self.existing_load_balancing_file_path)
            om("Successfully copied to: " + os.path.join(self.sim_data_input, load_balance_filename))
            
        om("", style = 'bold')
        
        
            
        # generate migration file if existing migration file is not provided and migration generation is requested
        if not self.existing_migration_file_path and self.migration_matrix_file_path:
            
            # instantiate a migration generator; default is geo-graph topology w/ gravity link rates model
            # todo: expose link rates/topology parameters to user
            
            om("generating migration graph and link rates...", style = 'bold') 
            
            mg = MigrationGenerator(os.path.join(self.sim_data_input, demographics_output_file), self.migration_matrix_file_path, graph_topo_type = 'geo-graph', link_rates_model_type = 'gravity')
            mg.generate_link_rates()
            mg.save_link_rates_to_txt(os.path.join(self.log_path, 'rates.txt'))
            
            om("Link rates log saved to: " + os.path.join(self.log_path, 'rates.txt'))


            om("generating migration binary...", style = 'bold') 
            migration_filename = self.cb.get_param('Local_Migration_Filename')
            MigrationGenerator.link_rates_txt_2_bin(os.path.join(self.log_path, 'rates.txt'), os.path.join(self.sim_data_input, migration_filename))
            
            om("Migration binary saved to: " + os.path.join(self.sim_data_input, migration_filename))
            
            
            om("generating migration json header...", style = 'bold') 
            MigrationGenerator.save_migration_header(os.path.join(self.sim_data_input, demographics_output_file))
            
            om("Migration header saved to: " + os.path.join(self.sim_data_input, demographics_output_file))
            
        else: #if existing migration files are provided, copy them to the right places
            
            om("Looking for existing migration binary and header...", style = 'bold')
            
            shutil.copy(self.existing_migration_file_path, os.path.join(self.sim_data_input, migration_filename))
            om("Existing binary found at : " + self.existing_load_balancing_file_path)
            om("Successfully copied to: " + os.path.join(self.sim_data_input, migration_filename))
            
            shutil.copy(self.existing_migration_file_path + '.json', os.path.join(self.sim_data_input, migration_filename + '.json'))
            om("Existing header found at : " + self.existing_load_balancing_file_path)
            om("Successfully copied to: " + os.path.join(self.sim_data_input, migration_filename))
            

        om("", style = 'bold') 
        
        
        # generate immune initialization overlays if existing ones are not provided and immune overlays are requested along with the provided required parameters
        overlay_file_names = [] # immune overlay filenames to be used in spatial simulation
        
        if not self.existing_immunity_files_paths and self.immunity_burnin_meta_file_path and self.nodes_params_input_file_path:
            
            om("generating immunity initialization overlays...", style = 'bold')

            # generate overlays at remote/local location    
            ig = ImmunityOverlaysGenerator(os.path.join(self.sim_data_input, demographics_output_file), self.immunity_burnin_meta_file_path, os.path.join(self.sim_data_input, self.geography), self.nodes_params_input_file_path)
                
            # generate overlays
            overlay_file_names = ig.generate_immune_overlays()
            
        else: # if existing immune initialization overlays are provided use them to configure the demographics file
            
            om("copying existing immunity initialization overlays...", style = 'bold')
            
            #copy all provided files to the right directory
            for immune_overlay_file_path in self.existing_immunity_files_paths:
                shutil.copy(immune_overlay_file_path, os.path.join(self.sim_data_input, self.geography))
                overlay_file_names.append(os.path.basename(immune_overlay_file_path)) # assuming file name does not end with a slash, in which case the basename would be empty
                om("Existing immune overlay " + immune_overlay_file_path)  
                om("Successfully copied to " + os.path.join(self.sim_data_input, self.geography))
        
        #update demographics files
        demographics_files = self.cb.get_param('Demographics_Filenames')
        for immune_overlay_file in overlay_file_names:
            demographics_files.append(os.path.join(self.geography, immune_overlay_file))
         
        self.cb.update_params({
                               'Enable_Immunity_Initialization_Distribution':1,
                               'Demographics_Filenames':demographics_files
                               })
            
        om("", style = 'bold')
      
        if self.log:
            
            om("storing logs", style = 'bold')
            
            # save demographics file in log dir
            with open( os.path.join(self.log_path, self.name + '_demographics_log.json' ),'w' ) as demo_f:
                json.dump(demographics, demo_f, indent = 4)
            
            om("LOG: demogrpahics file stored at " + os.path.join(self.log_path, self.name + '_demographics_log.json' ))
            
            # save load balance visualization in log dir
            lb.save_load_balance_figure(os.path.join(self.log_path, self.name + '_loadbalance.png'))
            
            om("LOG: load balance visualization stored at " + os.path.join(self.log_path, self.name + '_loadbalance.png'))
            
            if self.migration_matrix_file_path:
                # if migration file was provided save migration binary, header and routes visualization in log directory
                migration_filename = self.cb.get_param('Local_Migration_Filename')

            
            shutil.copy(os.path.join(self.sim_data_input, migration_filename), os.path.join(self.log_path, self.name + '_migration.bin'))
            om("LOG: migration binary stored at " + os.path.join(self.log_path, self.name + '_migration.bin'))
            
             
            shutil.copy(os.path.join(self.sim_data_input, migration_filename + '.json'), os.path.join(self.log_path, self.name + '_migration.bin.json'))
            om("LOG: migration binary stored at " + os.path.join(self.log_path, self.name + '_migration.bin.json'))
        
            MigrationGenerator.save_migration_visualization(os.path.join(self.log_path, self.name + '_demographics_log.json' ), os.path.join(self.log_path, self.name + '_migration.bin'), os.path.join(self.log_path))
            om("LOG: migration network stored in " + os.path.join(self.log_path))    
               
            if self.immunity_burnin_meta_file_path and self.nodes_params_input_file_path:
                # what would be a good immunity log? One could store the immune overlays in the log directory...
                # for now nothing is logged
                pass
            
        
        om("", style = 'bold')  
        om("setup success", style = 'bold')    
        om("", style = 'bold')  
        om("Proceeding to run experiment " + self.name)
        om("", style = 'bold')
        
        return
    


    def create_dirs(self):
        """
        Create the directories
        """
        # Current path
        if (not os.path.exists(self.current_path)):
            os.mkdir(self.current_path)

        # Output path
        if (not os.path.exists(self.output_path)):
            os.mkdir(self.output_path)

        # Logging
        if (self.log and not os.path.exists(self.log_path)):
            os.mkdir(self.log_path)