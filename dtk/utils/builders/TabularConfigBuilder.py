import os
from simtools.SimConfigBuilder import SimConfigBuilder
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.parsers.JSON import json2dict

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

    def __init__(self, plugin_info_json, plugin_files_json, plugin_files_dir, **kwargs):

        self.plugin_info_json = json2dict(plugin_info_json)
        self.plugin_files_json = json2dict(plugin_files_json)
        self.plugin_files_dir = plugin_files_dir

        self.templates = {}

        self.load_templates()

        static_params = self.plugin_info_json['Static_Parameters']
        print static_params
        self.static_param_map = self.build_static_param_map(static_params)
        # DJK TODO: handle kwargs
        #self.static_param_map = self.build_static_param_map(static_params + **kwargs)

        self.update_all_params( self.static_param_map )

    def build_static_param_map(self, params):
        static_param_map = {}
        for param in params:
            print "Splitting %s" % param
            split = param.split('.')
            if len(split) == 1:
                raise RuntimeError('Parameter \'' + param + '\' does not contain a period. Parameter names should be CONFIG.something, CAMPAIGN.something, or DEMOGRAPHICS.something.')
            param_type = split[0]
            param_address = '.'.join(split[1:])

            if param_type in static_param_map:
                static_param_map[param_type].append(param_address)
            else:
                static_param_map[param_type] = param_address

        return static_param_map

    def load_templates(self):
        for k in self.plugin_files_json.keys():
            for plugin_filename in self.plugin_files_json[k]:
                fn = os.path.join( self.plugin_files_dir, plugin_filename)
                self.Log('Loading %s as %s' % (fn, k))
                plugin_file = json2dict(fn)
                self.add_template_file( k, plugin_file)

    def add_template_file(self, type, filecontents):
        if type not in self.templates:
            self.templates[type] = [filecontents]
        else:
            self.templates[type].append(filecontents)

    def update_all_params(self, static_params):
        for template_type in self.templates.keys():
            for template in self.templates[template_type]:
                self.update_params(template, template_type, validate=False)

    def Log(self, msg):
        print(msg)

    @property
    def params(self):
        return self.templates

    def update_params(self, params, template_type, validate=False):
        # DJK EDITING HERE!!!
        #if template_type == self.config_template_key:
        #    for config_template in self.templates[template_type]:




        if not validate:
            self.params.update(params)
        else:
            for k, v in params.items():
                self.validate_param(k)
                logger.debug('Overriding: %s = %s' % (k, v))
                self.set_param(k, v)
        return params  # for ModBuilder metadata

    def set_param(self, param, value):
        print "-----------------------------------------------"

        """
        Set parameter in the config/campaign.

        The current supported syntax for the param argument is the following:
        - parameter
            A simple parameter. Will assume it is a parameter in the config["parameters"]. For example: Rainfall_Scale_Factor

        - CONFIG.path.parameter
            A parameter accessible in the CONFIG file at path. For example: CONFIG.Vector_Species_Params.arabiensis.Acquire_Modifier

        - CAMPAIGN.event_name.path.parameter / CAMPAIGN.event_index.path.parameter
            A parameter accessible in the CAMPAIGN file at path. The event needs to either have a name or an index
            For example: CAMPAIGN.ART for all females in 2025.Event_Coordinator_Config.Demographic_Coverage
            CAMPAIGN.3.Event_Coordinator_Config.Intervention_Config.Incubation_Period_Override

        - DRUG.drug.parameter
            A drug parameter for a given drug. For example: DRUG.Primaquine.Bodyweight_Exponent

        - VECTOR.vector.path.parameter
            Parameter for a given vector.
            Note that if Required_Habitat_factor is in the path, it is possible to specify which habitat by using: VECTOR.arabiensis.Required_Habitat_Factor.TEMPORARY_RAINFALL

        :param param:
        :param value:
        :return:
        """
        file="CONFIG"
        tag=False
        cleaned_param = ""

        if "CONFIG" in param:
            # e.g. CONFIG.Vector_Species_Params.arabiensis.Acquire_Modifier
            # Removes the CONFIG. part
            cleaned_param = param.replace("CONFIG.","")


        elif "VECTOR" in param:
            # e.g. VECTOR.arabiensis.Required_Habitat_Factor.TEMPORARY_RAINFALL
            # Find the index of the current selected habitat and pass the correct path to the cb
            cleaned_param = param.replace("VECTOR.","Vector_Species_Params.")
            if "Required_Habitat_Factor" in param:
                habitat = cleaned_param.split('.')[-1]
                vector_species = cleaned_param.split('.')[1]
                if not habitat.isdigit():
                    # The habitat is a string and not an index, replace it by the index
                    habitat_index = self.config["parameters"]["Vector_Species_Params"][vector_species]["Habitat_Type"].index(habitat)
                    cleaned_param = cleaned_param.replace(habitat,str(habitat_index))


        elif "DRUG" in param:
            # e.g. DRUG.Artemether.Drug_Adherence_Rate
            cleaned_param = param.replace("DRUG","Malaria_Drug_Params")


        elif "CAMPAIGN" in param and ".DRUG." in param:
            # particular case for drug campaigns generated by add_drug_campaign => just tag
            tag = True

        elif "CAMPAIGN" in param:
            file = "CAMPAIGN"
            event = param.split('.')[1]

            # In the case of the event being specified by ID instead of name
            if not event.isdigit():
                # Find the event index
                event_index = 0
                for event_data in self.campaign["Events"]:
                    if "Event_Name" in event_data.keys() and event_data["Event_Name"] == event:
                        break
                    event_index+=1

                # If the index doesnt exist => just consider as a tag
                if event_index >= len(self.campaign["Events"]):
                    file = "CONFIG"
                    tag = True
                else:
                    # Replace the name by the index
                    cleaned_param = param.replace(".%s." % event, ".%s." % event_index)
                    cleaned_param = cleaned_param.replace("CAMPAIGN.","")
            else:
                # The event was already a digit -> just remove the CAMPAIGN.
                cleaned_param = param.replace("CAMPAIGN.","")

        elif "HABSCALE" in param:
            # HABSCALE will already be set by another function. We only need to take care of tagging it in the config
            tag=True

        else:
            # Just set the param if no shortcut used
            cleaned_param = param

        # First get the correct file
        if file == "CONFIG":
            current_file = self.config["parameters"]
        else:
            current_file = self.campaign["Events"]

        # If it is consider a tag -> just add it to the config without any other treatment
        if tag:
            current_file[param] = value
            return {param:value}

        # Go through the path if there is a path
        if "." in cleaned_param:
            current_parameter = current_file
            # The path is everything except the last item of the split which represent the parameter
            for path_step in cleaned_param.split('.')[:-1]:
                # If the step is a number, we are in a list, we need to cast the step to int
                current_parameter = current_parameter[self.cast_value(path_step)]

            # Assign the casted value to the parameter but same as for the path_step we need to cast to int if
            # its a list index and not a dictionary key
            last_step = cleaned_param.split('.')[-1]
            current_parameter[self.cast_value(last_step)] = self.cast_value(value)

        else:
            # No path => simply assign
            current_file[cleaned_param] = self.cast_value(value)

        # For the tags return the non cleaned parameters so the parser can find it
        return {param:value}

    def file_writer(self, write_fn):
        # DJK Note: want to maintain user's filenames

        dump = lambda content: json.dumps(content, sort_keys=True, indent=4)

        self.set_param('Campaign_Filename','campaign.json')
        write_fn('campaign', dump(self.campaign))

        if self.custom_reports:
            self.set_param('Custom_Reports_Filename', 'custom_reports.json')
            write_fn('custom_reports', dump(format_reports(self.custom_reports)))

        for name, content in self.demog_overlays.items():
            self.append_overlay('%s.json' % name)
            write_fn(name, dump(content))

        write_fn('config', dump(self.config))

        write_fn('emodules_map', dump(self.emodules_map))
