import json

class WorkOrderGenerator:
    def __init__(self, demographics_file_path, wo_output_path, project_info="IDM-Democratic_Republic_of_the_Congo",
                 include_non_pop=True, shape_id="", resolution="30", parameters=['tmean', 'humid', 'rain'],
                 start_year='2009', num_years="4", nan_check=True, idRef = 'Gridded world grump2.5arcmin'):
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
        self.migration = False  # expose as parameter
        self.id_reference = idRef
        # self.id_reference = str(time.time())
        self.path = ''

    def wo_2_dict(self):
        wo = {'RequestType': self.request_type,
              'DemographicsPath': self.demographics_file_path,
              'WorkItem_Type': self.work_item_type,
              'PluginInfo': self.plugin_info,
              'Project': self.project_info,
              'Region': self.region,
              'IncludeNonPop': self.include_non_pop,
              'ShapeId': '',
              'Resolution': self.resolution,
              'Parameters': self.parameters,
              'StartYear': self.start_year,
              'NumYears': self.num_years,
              'NaNCheck': self.nan_check,
              'Migration': self.migration,
              'IdReference': self.id_reference,
              'ProjectRoot':'v2014'
        }

        # add the work order items
        # wo['Path'] = self.path

        # add nodes from demographics file
        with open(self.demographics_file_path, 'r') as demo_f:
            demographics = json.load(demo_f)

            # generate node list for work order
            for node in demographics['Nodes']:
                self.node_list.append(node['NodeID'])

        # wo['NodeList'] = self.node_list

        return wo

    def set_project_info(self, project_info):
        self.project_info = project_info

    def set_include_non_pop(self, include_non_pop):
        self.include_non_pop = include_non_pop

    def set_shape_id(self, shape_id):
        self.shape_id = shape_id

    def set_resolution(self, resolution):
        self.resolution = resolution

    def set_parameters(self, parameters):
        self.parameters = parameters

    def set_start_year(self, start_year):
        self.start_year = start_year

    def set_num_years(self, num_years):
        self.num_years = num_years

    def set_nan_check(self, nan_check):
        self.nan_check = nan_check

    def wo_2_json(self):
        with open(self.wo_output_path, 'w') as wo_f:
            json.dump(self.wo_2_dict(), wo_f, indent=3)
