import sys # temp

import os
import json
from simtools.SimConfigBuilder import SimConfigBuilder
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.builders.TemplateContainer import TemplateContainer
from dtk.interventions.empty_campaign import empty_campaign

# TODO: Can the config file be selected dynamically?

class TabularConfigBuilder(SimConfigBuilder):
    '''
    A class for configuing simulation input files.  

    The user provides several "template" files for:
    * simulation configuration (config.json)
    * intervention configuration (campaign.json)
    * demographics

    Example PluginFiles.json:
    {
        "CONFIG_TEMPLATE": [ "Config_Template.json" ],
        "CAMPAIGN_TEMPLATE": [ "Campaign_Baseline.json", "Campaign_Intervention.json" ],
        "DEMOGRAPHICS_TEMPLATE": [ "Demographics_Basline.json", "Demographics_Overlay_WithRiskGroups.json", "Demographics_Overlay_WithoutRiskGroups.json" ]
    }

    Selection of and modification to these template files are described by
    1. a list of "static" parameters, and
    2. a table of "dynamic" parameters.

    Static parameters are set for all simulations.

    The dynamic parameter table has a "Header" and "Table."
    Header lists the addresses of the parameters to modify.
    Each row of Table gives a value to place at each parameter address.

    Note that 

    One or more Run_Number values can be placed in the dynamic parameters.
    Alternatively, "CONFIG.Run_Number" can be included in the header to specify the random number seed per-simulation.

    Example PluginInfo.json:

    { 
        "Static_Parameters": 
        { 
            "CONFIG.Simulation_Duration": 20075
        },
        "Dynamic_Parameters": 
        { 
            "Run_Number": [ 1 ],
            "Header": [ "CONFIG.Base_Infectivity", "CONFIG.Male_To_Female_Relative_Infectivity_Multipliers", "CAMPAIGN.Start_Year__KP_Seeding_Year", "CAMPAIGN.Demographic_Coverage__KP_Seeding_15_24", "CAMPAIGN.Demographic_Coverage__KP_Seeding_25_49", "CAMPAIGN.Demographic_Coverage__KP_Seeding_50_65", "CAMPAIGN.Actual_IndividualIntervention_Config__KP_PreART_Link.Ramp_Min", "CAMPAIGN.Actual_IndividualIntervention_Config__KP_PreART_Link.Ramp_Max", "CAMPAIGN.Actual_IndividualIntervention_Config__KP_PreART_Link.Ramp_MidYear", "CAMPAIGN.Actual_IndividualIntervention_Config__KP_ART_Link.Ramp_Max", "CAMPAIGN.Actual_IndividualIntervention_Config__KP_ART_Link.Ramp_MidYear", "DEMOGRAPHICS.Society__KP_Bulawayo.TRANSITORY.Relationship_Parameters.Condom_Usage_Probability.Max", "CONFIG.Run_Number" ],
            "Table": 
                [
                [ 0.0011999999999999999, [ 3, 3, 1.5 ], 1978, 0.01, 0.01, 0.01, 0.46000000000000002, 0.69999999999999996, 2002, 0.90000000000000002, 2005, 0.34999999999999998, 587045 ], 
            [ 0.00071935215239709183, [ 2.662977533792704, 2.662977533792704, 1.7195102480699762 ], 1975.8302412806222, 0.011165079195963663, 0.0096554563061547315, 0.0094650487722785955, 0.4645260885736241, 0.83474719797989794, 2001.7224094679466, 0.91616878666025148, 2006.2564531906496, 0.361928436657381, 207743 ], 
                [ 0.0013897258152301287, [ 2.842913974090977, 2.842913974090977, 1.9874081438447095 ], 1980.8909929884808, 0.0098585163613047026, 0.0095463421925513908, 0.010048044679951195, 0.54610728362836736, 0.74867031201512302, 2002.9775305952046, 0.79265890317797127, 2005.4801136440851, 0.40370834139636114, 301247 ]
                ]
        }
    }
    '''

    config_template_key = 'CONFIG_TEMPLATE'    # handled differently from other template files
    campaign_template_key = 'CAMPAIGN_TEMPLATE'    # handled differently from other template files
    demographics_template_key = 'DEMOGRAPHICS_TEMPLATE'    # handled differently from other template files

    def __init__(self, plugin_info_json, plugin_files_json, plugin_files_dir, **kwargs):

        self.template_container = TemplateContainer(plugin_files_json, plugin_files_dir)

        self.plugin_info_json = json2dict(plugin_info_json)

        configs = self.template_container.get_by_type(self.config_template_key)
        assert( len(configs) == 1 ) # one and only one config for now
        config = configs[0]
        if config is None:
            print "ERROR ----------------------------------" # TODO

        self.config = config
        try:
            self.config.get_param('Simulation_Type')
        except:
            print "ADDING SIMULATION_TYPE to CONFIG"
            self.config.set_param('Simulation_Type','None') # Simulation_Type is a required parameter of simtools

        self.campaign = empty_campaign
        cfn = self.config.get_param('Campaign_Filename')
        self.set_campaign(cfn)

        self.demog = []
        dfns = self.config.get_param('Demographics_Filenames')
        self.add_demographics(dfns)

        static_params = self.plugin_info_json['Static_Parameters']
        self.static_param_map = self.build_param_map(static_params)
        # DJK TODO: handle kwargs
        #self.static_param_map = self.build_static_param_map(static_params + **kwargs)

        self.update_params_for_all_templates( self.static_param_map )

    def set_campaign(self, new_campaign_filename):
        print "Setting campaign filename to %s" % new_campaign_filename
        campaign = self.template_container.get( new_campaign_filename )
        if campaign is not None:
            print "--> Found in template_container"
            self.campaign = campaign

    def reset_demographics(self):
        self.demog = [] # Need to delete old demographic templates?

    def add_demographics(self, new_demographics_filenames):
        print "Setting demographics filenames to", new_demographics_filenames
        for dfn in new_demographics_filenames:
            demog_template = self.template_container.get( dfn )
            if demog_template is not None:
                print "--> %s: from template" % dfn
                self.demog.append({'Filename':dfn, 'Template':demog_template}) # Append template
            else:
                print "--> %s: not in template_container" % dfn
                self.demog.append({'Filename':dfn, 'Template':None}) # Append demographics filename

    def build_param_map(self, params):
        param_map = {}
        for param,value in params.items():
            split = param.split('.')
            if len(split) == 1:
                raise RuntimeError('Parameter \'' + param + '\' does not contain a period. Parameter names should be CONFIG.something, CAMPAIGN.something, or DEMOGRAPHICS.something.')
            param_type = split[0]
            param_address = '.'.join(split[1:])

            if param_type in param_map:
                param_map[param_type].update( {param_address:value} )
            else:
                param_map[param_type] = {param_address:value}

        return param_map

    def update_params_for_all_templates(self, param_map):
        self.template_container.update_params(param_map)

    def map_and_update_params_for_all_templates(self, params):
        '''
        ew
        '''

        print "PARAMS",params
        param_map = self.build_param_map(params)
        print "PARAM_MAP",param_map
        self.update_params_for_all_templates(param_map)

    def Log(self, msg):
        print(msg)

    #@property
    #def params(self):
    #    return self.templates

    def set_param(self, param, value):
        if "." not in param:
            param_map = { self.config_template_key.replace('_TEMPLATE', '') + '.' + param : value}
        else:
            param_map = build_param_map(self, {param,value})
        print "TEMP", param_map
        self.update_params_for_all_templates(param_map)

        #self.params[param] = value
        return {param: value}  # for ModBuilder metadata

    def get_param(self, param, default=None):
        return self.config.get_param(param)

    def file_writer(self, write_fn):
        # DJK Note: want to maintain user's filenames

        dump = lambda content: json.dumps(content, sort_keys=True, indent=4)

        campaign_filename = self.config.get_param('Campaign_Filename')
        write_fn('campaign', dump(self.campaign.contents))  # TODO:Functional access or contained in template

        #if self.custom_reports:
        #    self.set_param('Custom_Reports_Filename', 'custom_reports.json')
        #    write_fn('custom_reports', dump(format_reports(self.custom_reports)))


        for demog in self.demog:
            print "DEMOG",demog
            filename = demog['Filename']
            template = demog['Template']

            self.config.append_demographics_overlay( filename )

            if template is not None:
                write_fn(filename.replace('.json', ''), dump(template.get_contents()))

        write_fn('config', dump(self.config.get_contents()))

        #write_fn('emodules_map', dump(self.emodules_map))
