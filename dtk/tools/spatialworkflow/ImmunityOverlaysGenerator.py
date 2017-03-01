import json
import os

from simtools.OutputParser import CompsDTKOutputParser as parser
from dtk.tools.demographics.compiledemog import CompileDemographics

from dtk.utils.ioformat.OutputMessage import OutputMessage as om
from simtools.Utilities.COMPSUtilities import COMPS_login


class ImmunityOverlaysGenerator(object):
    '''
    Create a set of immune overlays mapped to corresponding nodes 
    '''


    def __init__(self, demographics_file_path, immunity_burnin_meta_file_path, immune_overlays_path, nodes_params_file_path):

        self.immunity_burnin_meta_file_path = immunity_burnin_meta_file_path
        self.demographics_file_path = demographics_file_path
        self.immune_overlays_path = immune_overlays_path
        
        
        
        #to contain a dictionary of parameter keys and their corresponding values
        self.params_values = None
        
        
        # read nodes parameters
        
        '''
        a dictionary of node_labels to a set of parameters of the form
        {
            node_label1: {
                            param1: value,
                            param2: value,
                            ...
                         },
                         
            node_label2: {
                            param1: value,
                            param2: value,
                            ...
                         },
            ...
            
            parameter keys should match a subset of the simulation parameters tags as recorded in the immunity burnin experiments meta data json file;
            parameter keys are the same across nodes (e.g. the parameters of immune initialization burnin); 
            nodes can then be mapped to immune overlays corresponding to each node's parameters
        }
        
        '''
        
        with open(nodes_params_file_path,'r') as np_f:
            self.nodes_params = json.load(np_f)
            

        '''
        to contain a dictionary of nodes grouped by simulation parameters of the form
        {
            'value0_value0_value0..._':[{'NodeID':node_id1}, {'NodeID':node_id2}, {'NodeID':node_id3}, ...],
            'value0_value2_value0..._':[{'NodeID':node_id4}, {'NodeID':node_id5}, {'NodeID':node_id6}, ...],
            ...
        } 
        
        see group_nodes_by_params(self)
        '''
        self.nodes_by_params = None


    
    def group_nodes_by_params(self):
            
        # load the demographics file to map node_labels to node_ids
        with open(self.demographics_file_path, 'r') as demo_f:
            demographics = json.load(demo_f)
        
        # consider abstracting the node_label_2_id code to its own module; could be a singleton structure available to a bunch of classes
        node_label_2_id = {}
        for node in demographics['Nodes']:
            node_label = node['NodeAttributes']['FacilityName']
            node_id = node['NodeID']
            node_label_2_id[node_label] = node_id
            
        self.nodes_by_params = {}
    
        for node_label, params in self.nodes_params.iteritems():
            
            param_key = self.get_params_key(params.values())
                    
            if param_key in self.nodes_by_params:
                self.nodes_by_params[param_key].append({'NodeID':node_label_2_id[node_label]})
            else:
                self.nodes_by_params[param_key] = [{'NodeID':node_label_2_id[node_label]}]
        
        
    
    '''
    a helper function generating a string key for a set of parameter values;
    different ways to do that; this is a very simple one
    '''
    def get_params_key(self, param_values):
        
        param_key = ''
        for v in param_values:
            param_key += str(v) + '_'
            
        return param_key
    
    
    
    '''
    process json given by immunity_burnin_meta_file_path to extract 
    immunity burnin sweep experiments ids, output files, burnin simulations' parameters;
    '''
    def generate_immune_overlays(self):
        
        ''' 
        generate immune overlays; the json file format pointed to by self.immunity_burnin_meta_file_path is
         
        {
            exp_id1:path to experiment meta json file created in the folder indicated by sim_root in dtk_setup.cfg   
            exp_id2: --||--,
            ...
        }
        
        '''
        
        # group nodes by parameter 
        self.group_nodes_by_params()
        
        with open('nodes_by_param.json','w') as p_f:
            json.dump(self.nodes_by_params, p_f, indent = 4)
        
        
        # maintain a list of overlays' file paths so that they can be used by the spatial simulation later?
        overlays_list = []
        
        # open file containing paths to immune initialization burnin sweep meta files
        with open(self.immunity_burnin_meta_file_path, 'r') as imm_f:
            immun_meta_exps = json.load(imm_f)
            
            i = 0
            for exp_id, exp_path in immun_meta_exps.iteritems():
                
                with open(os.path.abspath(exp_path),'r') as meta_f:
                    exp_meta = json.load(meta_f)
                    
                    # find out if experiment has been run locally or remotely on hpc;
                    # that determines the simulation output folder location and structure
                    exp_location_type = exp_meta['location']
                    exp_name = exp_meta['exp_name']
                    
                    # do we have a helper function that determines the output directory of a simulation given simulation and experiment IDs (working both for COMPs and local)?
                    sim_dir_map = None
                    if exp_location_type == 'HPC':

                        from simtools.SetupParser import SetupParser
                        sp = SetupParser('HPC')
                        om("Pulling immunization data from COMPs.")
                        om("This requires a login.")

                        COMPS_login(sp.get('server_endpoint'))
                        om("Login success!")

                        sim_dir_map = parser.createSimDirectoryMap(exp_id)
                        
                        
                    # iterate through the experiments simulations;
                    for sim_id, sim_record in exp_meta['sims'].iteritems():
                        sim_output_path = ''
                                                
                        #for each simulation get the values of parameters relevant to the immune initialization burnin (i.e. the parameters 
                        # given by the keys in self.nodes_params)
                        
                        # the mapping between nodes and immune overlays below could be done more efficiently, but for the typical number of parameters the
                        # mapping below should work fine
                        
                        # get the parameter keys in the right order (see group_nodes_by_params(self) and get_params_key(self...); 
                        # the set of relevant parameters is the same across all nodes, so take the one from the first node
                        node_params = self.nodes_params.itervalues().next().keys()

                        param_values = [] 
                        for param in node_params:
                            if param in sim_record:
                                param_values.append(sim_record[param])

                        
                        # get nodes associated with this set of parameters
                        if self.get_params_key(param_values) in self.nodes_by_params:
                                                                                     
                            params_key = self.get_params_key(param_values)
                            nodes = self.nodes_by_params[params_key]


                            # for each simulation get its output immunity report
                            if exp_location_type == 'LOCAL':
                                sim_output_path = os.path.join(exp_meta['sim_root'], exp_name +'_' + exp_meta['exp_id'], sim_id, 'output')
                            elif exp_location_type == 'HPC':
                                sim_output_path = os.path.join(sim_dir_map[sim_id], 'output')
                                
                            immunity_report_file_path = os.path.join(sim_output_path, 'MalariaImmunityReport_AnnualAverage.json')
                            
    
                            # generate immune overlay
                            from dtk.tools.demographics.createimmunelayer import \
                                immune_init_from_custom_output_for_spatial as immune_init
                            immune_overlay_json = immune_init(
                                                              { 
                                                               "Metadata": {  
                                                                                "Author": "dtk-tools", 
                                                                                "IdReference": "Gridded world grump30arcsec", 
                                                                                "NodeCount": len(nodes) 
                                                                            }, 
                                                                "Nodes": nodes  
                                                                }, 
                                                                immunity_report_file_path,
                                                              )
                            
                            # save compiled overlay
                            overlay_file_name = params_key + exp_name + '.json'
                            overlay_file_path = os.path.join(self.immune_overlays_path, overlay_file_name)
                            with open(overlay_file_path, 'w') as imo_f:
                                json.dump(immune_overlay_json, imo_f)
                            
                            CompileDemographics(overlay_file_path, forceoverwrite=True)
                            
                            # add overlay location to overlay list
                            overlays_list.append(overlay_file_name)
                            
                    
                    
                print str(len(overlays_list)) + " immune initialization overlay files processed successfully!"
                        
        return overlays_list 
