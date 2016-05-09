import json

class WorkOrderGenerator():
    
    def __init(self, demographics_file_path, wo_output_path, project_info = "IDM-Zambia", include_non_pop = True, shape_id = "", resolution = "30", parameters = ['tmean', 'humid', 'rain'], start_year = '2005', num_years = "9", nan_check = True):
        
        self.demographics_file_path = demographics_file_path
        self.wo_output_path = wo_output_path
        self.request_type = "FromDemographics"
        self.work_item_type = "InputDataWorker"
        self.node_list = None
        self.plugin_info = []
        self.project_info = project_info
        self.region = ""
        self.include_non_pop = include_non_pop
        self.shape_id = shape_id
        self.resolution = resolution
        self.parameters = parameters
        self.start_year = start_year
        self.num_years = num_years
        self.nan_check = nan_check
    
    
    
    def generate_climate_wo_from_demographics(self):
        
        with open(self.demographics_file_path,'r') as demo_f:
            
            demographics = json.load(demo_f)
            
            #generate node list for wo
            
            for node in demographics['Nodes']:
                self.node_list.append(node['NodeID'])
            
            
                
                
    def wo_dict(self):
        wo = {}
        
        # add the work order items
        
        return wo
        
        
            
            