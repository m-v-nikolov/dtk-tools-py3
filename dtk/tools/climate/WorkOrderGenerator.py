import json

class WorkOrderGenerator():
    
    def __init__(self, demographics_file_path, wo_output_path, project_info = "IDM-Democratic_Republic_of_the_Congo", include_non_pop = True, shape_id = "", resolution = "30", parameters = ['tmean', 'humid', 'rain'], start_year = '2008', num_years = "5", nan_check = True):
        
        self.demographics_file_path = demographics_file_path
        self.wo_output_path = wo_output_path
        self.request_type = "FromDemographics"
        self.work_item_type = "InputDataWorker"
        self.node_list = []
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
    
                
    def wo_2_dict(self):
        
        wo = {}
        # add the work order items
        wo['RequestType'] = self.request_type
        wo['DemographicsPath'] = self.demographics_file_path
        wo['WorkItem_Type'] = self.work_item_type
        wo['PluginInfo'] = self.plugin_info
        wo['Project'] = self.project_info
        wo['Region'] = self.region
        wo['IncludeNonPop'] = self.include_non_pop
        wo['ShapeId'] = ''
        wo['Resolution'] = self.resolution
        wo['Parameters'] = self.parameters
        wo['StartYear'] = self.start_year
        wo['NumYears'] = self.num_years
        wo['NaNCheck'] = self.nan_check

        # add nodes from demographics file
        with open(self.demographics_file_path,'r') as demo_f:
            demographics = json.load(demo_f)
            
            #generate node list for work order
            for node in demographics['Nodes']:
                self.node_list.append(node['NodeID'])
                
        wo['NodeList'] = self.node_list
        
        return wo
        
    
    def wo_2_json(self):
        with open(self.wo_output_path,'w') as wo_f:
            json.dump(self.wo_2_dict(), wo_f, indent = 3)