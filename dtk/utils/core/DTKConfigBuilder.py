import os
import json

import dtk.generic.params as generic_params
import dtk.vector.params as vector_params
import dtk.malaria.params as malaria_params
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.reports.CustomReport import format as format_reports
from dtk.utils.parsers.JSON import json2dict, dict2json

# A class for building and modifying config/campaign files
class DTKConfigBuilder:

    def __init__(self, config={'parameters':{}}, campaign=empty_campaign):
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
        config = json2dict(config_name)
        campaign = json2dict(campaign_name) if campaign_name else empty_campaign
        return cls(config, campaign)

    def copy_from(self,other):
        self.__dict__ = other.__dict__.copy()

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