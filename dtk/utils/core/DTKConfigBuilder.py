import os
import json

import dtk.generic.params as generic_params
import dtk.vector.params as vector_params
import dtk.malaria.params as malaria_params
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.reports.CustomReport import format as format_reports

# A class for building and modifying config/campaign files
class DTKConfigBuilder:

    def __init__(self, config, campaign):
        self.config = config
        self.campaign = campaign
        self.demog_overlays = {}
        self.custom_reports = []
        self.dlls = set()

    @classmethod
    def from_defaults(cls, sim_type=None):
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

        return cls(config, empty_campaign)

    @classmethod
    def from_files(cls, config_name, campaign_name=None):

        with open( config_name, "r" ) as configjson_file:
            config = json.loads( configjson_file.read() )

        if campaign_name:
            with open( campaign_name, "r" ) as campaignjson_file:
                campaign = json.loads( campaignjson_file.read() )
        else:
            campaign = empty_campaign

        return cls(config, campaign)

    def update_params(self, params):
        self.config["parameters"].update(params)

    def set_param(self, param, value):
        self.config["parameters"][param] = value

    def get_param(self, param, default=None):
        return self.config["parameters"].get(param, default)

    def add_event(self, event):
        self.campaign["Events"].append(event)

    def clear_events(self):
        self.campaign["Events"][:] = []

    def add_reports(self,*reports):
        for r in reports:
            self.custom_reports.append(r)
            self.dlls.add(r.get_dll_path())

    def dump_files(self, output_directory):

        if not os.path.exists(output_directory):
            os.makedirs(output_directory)

        with open( os.path.join( output_directory, "config.json"), "w" ) as config_file:
            self.config["parameters"]["Campaign_Filename"] = "campaign.json"
            if self.custom_reports:
                with open( os.path.join( output_directory, "custom_reports.json"), "w" ) as custom_reports_file:
                    custom_reports_file.write( json.dumps( format_reports(self.custom_reports), sort_keys=True, indent=4 ) )
                self.config["parameters"]["Custom_Reports_Filename"] = "custom_reports.json"
            config_file.write( json.dumps( self.config, sort_keys=True, indent=4 ) )

        with open( os.path.join( output_directory, "campaign.json"), "w" ) as campaign_file:
            campaign_file.write( json.dumps( self.campaign, sort_keys=True, indent=4 ) )

    def dump_files_to_string(self):

        files={}

        files['campaign'] = json.dumps( self.campaign, sort_keys=True, indent=4 )

        self.config["parameters"]["Campaign_Filename"] = "campaign.json"
        files['config'] = json.dumps( self.config, sort_keys=True, indent=4 )

        if self.custom_reports:
            self.config["parameters"]["Custom_Reports_Filename"] = "custom_reports.json"
            files['custom_reports'] = json.dumps( format_reports(self.custom_reports), sort_keys=True, indent=4 )

        return files