import os
import time
import glob
import shutil

class ClimateGenerator():
    
    
    def __init__(self, climate_files_gen_path, ld_tool_path, work_order_path, climate_files_output_path):
        
        self.climate_files_gen_path = climate_files_gen_path 
        self.ld_tool_path  = ld_tool_path
        self.work_order_path = work_order_path
        self.climate_files_output_path = climate_files_output_path
        
    
    def generate_climate_files(self):
        
        # below is something hacky (not good)
        # need to switch subprocess, capture output, check for errors, etc.; below is just a proof of concept
        # have a robust file check and handling mechanism
        # need to check if large_data.py does similar stuff 
        os.system(self.ld_tool_path + "ld --createdtkfiles " + self.work_order_path + " " + self.climate_files_output_path)
        os.system(self.ld_tool_path + "ld --flatrootdir " + self.climate_files_output_path)
        
        files_ready = False 
        while not os.path.exists(self.climate_files_output_path) and not files_ready:
            time.sleep(0.01)
            
            if os.path.exists(self.climate_files_output_path):
                rain_re = os.path.abspath(self.climate_files_output_path + '/*rain*')
                humidity_re = os.path.abspath(self.climate_files_output_path + '/*humidity*')
                temperature_re = os.path.abspath(self.climate_files_output_path + '/*temperature*')
                if len(glob.glob(rain_re)) > 0 and len(glob.glob(humidity_re)) and len(glob.glob(temperature_re)):
                    
                        # copy files to the appropriate data input directory
                        shutil.copy(glob.glob(rain_re)[0], self.climate_files_output_path)
                        shutil.copy(glob.glob(humidity_re)[0], self.climate_files_output_path)
                        shutil.copy(glob.glob(temperature_re)[0], self.climate_files_output_path) 
                    
                        files_ready = True