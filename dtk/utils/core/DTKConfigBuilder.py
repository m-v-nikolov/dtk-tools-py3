import os
import json
import logging

import dtk.generic.params as generic_params
import dtk.vector.params as vector_params
import dtk.malaria.params as malaria_params
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.reports.CustomReport import format as format_reports
from dtk.utils.parsers.JSON import json2dict, dict2json

# A class for building and modifying config/campaign files
class DTKConfigBuilder:

    def __init__(self, config={'parameters':{}}, campaign=empty_campaign, **kwargs):
        self.config = config
        self.campaign = campaign
        self.demog_overlays = {}
        self.custom_reports = []
        self.dlls = set()
        self.update_params(kwargs, validate=True)

    @classmethod
    def from_defaults(cls, sim_type=None, **kwargs):
        if not sim_type:
            raise Exception("Instantiating DTKConfigBuilder from defaults requires a sim_type argument, e.g. 'MALARIA_SIM'.")

        # Get generic base config
        config = { "parameters" : generic_params.params }

        # Add vector/malaria simulation-specific parameters
        if sim_type == "MALARIA_SIM":
            config["parameters"].update(vector_params.params)
            config["parameters"].update(malaria_params.params)

        elif sim_type == "VECTOR_SIM":
            config["parameters"].update(vector_params.params)

        elif sim_type == "VECTOR_SIM_VIVAX_SEMITROPICAL":
            config["parameters"].update(vector_params.params)
            config["parameters"].update(vector_params.vivax_semitropical_params)
            sim_type = "VECTOR_SIM"

        elif sim_type == "VECTOR_SIM_VIVAX_CHESSON":
            config["parameters"].update(vector_params)
            config["parameters"].update(vector_params.vivax_chesson_params)
            sim_type = "VECTOR_SIM"

        else:
            raise Exception("Don't recognize sim_type argument = %s" % sim_type)

        config["parameters"]["Simulation_Type"] = sim_type

        return cls(config, empty_campaign, **kwargs)

    @classmethod
    def from_files(cls, config_name, campaign_name=None):
        config = json2dict(config_name)
        campaign = json2dict(campaign_name) if campaign_name else empty_campaign
        return cls(config, campaign)

    def copy_from(self,other):
        self.__dict__ = other.__dict__.copy()

    def update_params(self, params, validate=False):
        if not validate:
            self.config["parameters"].update(params)
        else:
            for k, v in params.items():
                self.validate_param(k)
                logging.debug('Overriding: %s = %s' % (k, v))
                self.set_param(k, v)

    def cast_value(self,value):
        """
        Try to cas a value to float or int or string
        :param value:
        :return:
        """
        # The value is already casted
        if not isinstance(value, str):
            return value

        # We have a string so test if only digit
        if value.isdigit():
            casted_value =  int(value)
        else:
            try:
                casted_value = float(value)
            except:
                casted_value = value

        return casted_value


    def set_param(self, param, value):
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

    def get_param(self, param, default=None):
        return self.config["parameters"].get(param, default)

    def validate_param(self, param):
        if param not in self.config["parameters"]:
            raise Exception('No parameter named %s' % param)
        return True

    def enable(self, param):
        param = 'Enable_' + param
        self.validate_param(param)
        self.set_param(param, 1)

    def disable(self, param):
        param = 'Enable_' + param
        self.validate_param(param)
        self.set_param(param, 0)

    def add_event(self, event):
        self.campaign["Events"].append(event)

    def clear_events(self):
        self.campaign["Events"][:] = []

    def add_reports(self,*reports):
        for r in reports:
            self.custom_reports.append(r)
            self.dlls.add(r.get_dll_path())

    def append_overlay(self,demog_file):
        self.config['parameters']['Demographics_Filenames'].append(demog_file)

    def add_demog_overlay(self,name,content):
        if name in self.demog_overlays:
            raise Exception('Already have demographics overlay named %s'%name)
        self.demog_overlays[name]=content

    def dump_files(self, working_directory):
        if not os.path.exists(working_directory):
            os.makedirs(working_directory)
        def write_file(name,content):
            dict2json(os.path.join(working_directory,'%s.json'%name), content)
        self.file_writer(write_file)

    def dump_files_to_string(self):
        files={}
        def update_strings(name,content):
            files[name] = content
        self.file_writer(update_strings)
        return files

    def file_writer(self,write_fn):

        dump = lambda content: json.dumps(content, sort_keys=True, indent=4)

        self.set_param('Campaign_Filename','campaign.json')
        write_fn('campaign', dump(self.campaign))

        if self.custom_reports:
            self.set_param('Custom_Reports_Filename','custom_reports.json')
            write_fn('custom_reports', dump(format_reports(self.custom_reports)))

        for name,content in self.demog_overlays.items():
            self.append_overlay('%s.json'%name)
            write_fn(name, dump(content))

        write_fn('config',dump(self.config))

def set_param(cb, param, value):
   return cb.set_param(param,value)