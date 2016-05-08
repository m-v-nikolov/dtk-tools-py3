import os
import json
import csv
from datetime import datetime

from dtk.tools.demographics.node import Node, nodeid_from_lat_lon 

class DemographicsGenerator():
    '''
    Generates demographics file based on population input file.
    The population input file is csv with structure
    
    node_label*, lat, lon, pop*
    
    *-ed columns are optional
    '''
    
    def __init__(self, cb, population_input_file, demographics_type = 'static', res_in_arcsec = 30.0, update_demographics = None):
        
        """
        Initialize the SpatialManager
        :param cb: config builder reference, updated after the demographics file is generated.
        :param demographics_type: could be 'static', 'growing' or a different type; currently only static is implemented in generate_nodes(self)
        :param res_in_arsec: sim grid resolution
        :param update_demographics: provide the user with a chance to update the demographics file before it's written via a user-defined function; (e.g. scale larval habitats based on initial population per node in the demographics file) see generate_demographics(self) 
        :return:
        """
        
        self.population_input_file = population_input_file
        
        self.cb = cb
                
        self.demographics_type = demographics_type
        
        self.res_in_arcsec = res_in_arcsec
        
        self.res_in_degrees = self.res_in_arcsec/3600.0
        
        self.update_demographics = update_demographics

        # list of DTK nodes
        self.nodes = []
        
        # demographics data dictionary (working DTK demographics file when dumped as json)
        self.demographics = None
        
        self.default_pop = None
        
    
                                        
    def set_demographics_type(self, demographics_type):
        self.demographics_type = demographics_type
        
    def set_update_demographics(self, update_demographics):
        self.update_demographics = update_demographics # callback function
        
    def set_res_in_arcsec(self, res_in_arcsec):
        self.res_in_arcsec = res_in_arcsec
    
    
    '''
    generate a list of dtk nodes from input csv
    '''
    def process_input(self):
        
        with open(self.population_input_file,'r') as pop_csv:
            reader = csv.DictReader(pop_csv)

            lat = None
            lon = None
            node_label = None
            pop = 1000
            
            for row in reader:
                if not 'lat' in row:
                    raise ValueError('Column lat is required in input population file.')
                else:
                    lat = row['lat']
                
                if not 'lon' in row:
                    raise ValueError('Column lon is required in input population file.')
                else:
                    lon = row['lon']
                
                if 'node_label' in row:
                    node_label = row['node_label']
                else:
                    node_label = nodeid_from_lat_lon(lat, lon, self.res_in_degrees)
                     
                if 'pop' in row:
                    pop = row['pop']
                else:
                    self.default_pop = pop
                    
                self.nodes.append(Node(lat, lon, pop, node_label))
                
    
    
    '''
    generate the defaults section of the demographics file
    '''
    def generate_defaults(self):
        '''
        all of the below can be taken care of by a generic Demographics class
        (see note about refactor in dtk.generic.demographics)
        '''
    
        distribution_types = {
                                "CONSTANT_DISTRIBUTION" : 0,
                                "UNIFORM_DISTRIBUTION" : 1,
                                "GAUSSIAN_DISTRIBUTION" : 2,
                                "EXPONENTIAL_DISTRIBUTION" : 3,
                                "POISSON_DISTRIBUTION" : 4,
                                "LOG_NORMAL" : 5,
                                "BIMODAL_DISTRIBUTION" : 6
                                }
    
        # currently support only static population; after demographics related refactor this whole method will likely disappear anyway 
        if self.demographics_type == 'static':
            self.cb.set_param("Birth_Rate_Dependence", "FIXED_BIRTH_RATE")
        else:
            raise ValueError("Demographics type " + str(self.demographics_type) + " is not implemented!")
        
        exponential_age_param = 0.000118
        population_removal_rate = 45
        mod_mortality = {
                        "NumDistributionAxes": 2,
                        "AxisNames": [ "gender", "age" ],
                        "AxisUnits": [ "male=0,female=1", "years" ],
                        "AxisScaleFactors": [ 1, 365 ],
                        "NumPopulationGroups": [ 2, 1 ],
                        "PopulationGroups": [
                            [ 0, 1 ],
                            [ 0 ]
                        ],
                        "ResultUnits": "annual deaths per 1000 individuals",
                        "ResultScaleFactor": 2.74e-06,
                        "ResultValues": [
                            [ population_removal_rate ],
                            [ population_removal_rate ]
                        ]
                    }

        individual_attributes = {
                                 "MortalityDistribution": mod_mortality,
                                 "AgeDistributionFlag": distribution_types["EXPONENTIAL_DISTRIBUTION"],
                                 "AgeDistribution1": exponential_age_param,
                                 "RiskDistribution1": 1, 
                                 "PrevalenceDistributionFlag": 1, 
                                 "AgeDistribution2": 0, 
                                 "PrevalenceDistribution1": 0.1, 
                                 "PrevalenceDistribution2": 0.2, 
                                 "RiskDistributionFlag": 0, 
                                 "RiskDistribution2": 0, 
                                 "MigrationHeterogeneityDistribution1": 1, 
                                 "ImmunityDistributionFlag": 0, 
                                 "MigrationHeterogeneityDistributionFlag": 0, 
                                 "ImmunityDistribution1": 1, 
                                 "MigrationHeterogeneityDistribution2": 0, 
                                 "AgeDistributionFlag": 3, 
                                 "ImmunityDistribution2": 0
                                 }
                                 
        node_attributes = {
                            "Urban": 0, 
                            "AbovePoverty": 0.5, 
                            "Region": 1, 
                            "Seaport": 0, 
                            "Airport": 0, 
                            "Altitude": 0
                           }
        
        if self.default_pop:
            node_attributes.update({"InitialPopulation":self.default_pop})
    
        defaults = {
                    'IndividualAttributes': individual_attributes,
                    'NodeAttributes': node_attributes,
                    }
        
        return defaults
    
     
    '''       
    this function is currently replicated to a large extent in dtk.tools.demographics.node.nodes_for_DTK() but perhaps should not belong there
    it probably belongs to a generic Demographics class (also see one-liner note about refactor in dtk.generic.demographics)
    '''
    def generate_nodes(self):

        nodes = []
        for node in self.nodes:
            node_id = nodeid_from_lat_lon(float(node.lat), float(node.lon), self.res_in_degrees)
            node_attributes = node.toDict()
            
            if self.demographics_type == 'static':
                birth_rate = (float(node.pop)/(1000 + 0.0))*0.12329
                node_attributes.update({'BirthRate':birth_rate})
            else:
                # perhaps similarly to the DTK we should have error logging modes and good generic types exception raising/handling
                # to avoid code redundancy
                print self.demographics_type
                raise ValueError("Demographics type " + str(self.demographics_type) + " is not implemented!")
        
            nodes.append({'NodeID':node_id, 'NodeAttributes':node_attributes})
            
        return nodes
        
    
    
    '''
    generate demographics file metadata
    '''     
    def generate_metadata(self):
    
        metadata = {
                    "Author": "idm", 
                    "Tool": "dtk-tools", 
                    "IdReference": "Gridded world grump30arcsec", 
                    "DateCreated": str(datetime.now()), 
                    "NodeCount": len(self.nodes), 
                    "Resolution": self.res_in_arcsec
                    }
    
        return metadata
    
    
    
    '''
    return all demographics file components in a single dictionary; a valid DTK demographics file when dumped as json
    '''
    def generate_demographics(self):
        
        self.process_input()
        
        self.demographics = {}
        self.demographics['Nodes'] = self.generate_nodes()
        self.demographics['Defaults'] = self.generate_defaults()
        self.demographics['Metadata'] = self.generate_metadata()
        
        if self.update_demographics:
            # update demographics before dict is written to file, via a user defined function and arguments
            # self.update_demographics is a partial object (see python docs functools.partial) and self.update_demographics.func references the user's function 
            # the only requirement for the user defined function is that it needs to take a keyword argument demographics
            self.update_demographics(demographics = self.demographics)
        
        return self.demographics                