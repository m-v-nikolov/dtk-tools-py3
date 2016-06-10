import json
import logging
import os

from simtools import utils
from simtools.SimConfigBuilder import SimConfigBuilder

import dtk.generic.params as generic_params
import dtk.vector.params as vector_params
import dtk.malaria.params as malaria_params
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.reports.CustomReport import format as format_reports
from dtk.utils.parsers.JSON import json2dict, dict2json

logger = logging.getLogger(__name__)

class DTKConfigBuilder(SimConfigBuilder):
    '''
    A class for building, modifying, and writing
    required configuration files for a DTK simulation
    '''

    staged_dlls = {}  # caching to avoid repeat md5 and os calls

    def __init__(self, config={'parameters': {}}, campaign=empty_campaign, **kwargs):
        self.config = config
        self.campaign = campaign
        self.demog_overlays = {}
        self.input_files = {}
        self.custom_reports = []
        self.dlls = set()
        self.emodules_map = {'interventions': [],
                             'disease_plugins': [],
                             'reporter_plugins': []}
        self.update_params(kwargs, validate=True)

    @classmethod
    def from_defaults(cls, sim_type=None, **kwargs):
        '''
        Build up the default parameters for the specified simulation type.
        Start from required GENERIC_SIM parameters and layer VECTOR_SIM
        and also MALARIA_SIM default parameters as required.

        Configution parameter names and values may be passed as keyword arguments,
        provided they correspond to existing default parameter names.

        P.vivax disease parameters may be approximated using VECTOR_SIM simulations
        by passing either the VECTOR_SIM_VIVAX_SEMITROPICAL or VECTOR_SIM_VIVAX_CHESSON
        sim_type argument depending on the desired relapse pattern.
        '''

        if not sim_type:
            raise Exception("Instantiating DTKConfigBuilder from defaults requires a sim_type argument, e.g. 'MALARIA_SIM'.")

        config = {"parameters": generic_params.params}

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
    def from_files(cls, config_name, campaign_name=None, **kwargs):
        '''
        Build up a simulation configuration from the path to an existing
        config.json and optionally a campaign.json file on disk.
        '''

        config = json2dict(config_name)
        campaign = json2dict(campaign_name) if campaign_name else empty_campaign

        return cls(config, campaign, **kwargs)

    @property
    def params(self):
        return self.config['parameters']

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

    def add_reports(self, *reports):
        for r in reports:
            self.custom_reports.append(r)
            self.dlls.add(r.get_dll_path())

    def add_input_file(self, name, content):
        if name in self.input_files:
            logger.warn('Already have input file named %s, replacing previous input file.' % name)
        self.input_files[name] = content

    def append_overlay(self, demog_file):
        self.config['parameters']['Demographics_Filenames'].append(demog_file)

    def add_demog_overlay(self, name, content):
        if name in self.demog_overlays:
            raise Exception('Already have demographics overlay named %s' % name)
        self.demog_overlays[name] = content

    def get_commandline(self, exe_path, paths):
        eradication_options = {'--config': 'config.json', '--input-path': paths['input_root']}

        if 'python_path' in paths and paths['python_path'] != '':
            eradication_options['--python-script-path'] = paths['python_path']

        return utils.CommandlineGenerator(exe_path, eradication_options, [])

    def stage_required_libraries(self, dll_path, staging_root,assets_service = False):
        for dll_type, dll_name in self.dlls:
            # Try top retrieve the dll from the staged dlls
            staged_dll = self.staged_dlls.get((dll_type, dll_name), None)

            if not staged_dll:
                if not assets_service:
                    # If the assets service is not use, actually stage the dll file
                    staged_dll = utils.stage_file(os.path.join(dll_path, dll_type, dll_name),
                                                    os.path.join(staging_root, dll_type))
                else:
                    # If the assets service is used, assume that the dll is staged already
                    staged_dll = os.path.join(staging_root ,dll_name)
                # caching to avoid repeat md5 and os calls
                self.staged_dlls[(dll_type, dll_name)] = staged_dll

            # Add the dll to the emodules_map
            self.emodules_map[dll_type].append(staged_dll)

    def file_writer(self, write_fn):

        dump = lambda content: json.dumps(content, sort_keys=True, indent=4)

        write_fn(self.config['parameters']['Campaign_Filename'].replace('.json', ''), dump(self.campaign))

        if self.custom_reports:
            self.set_param('Custom_Reports_Filename', 'custom_reports.json')
            write_fn('custom_reports', dump(format_reports(self.custom_reports)))

        for name, content in self.demog_overlays.items():
            self.append_overlay('%s.json' % name)
            write_fn(name, dump(content))

        for name, content in self.input_files.items():
            write_fn(name, dump(content))

        write_fn('config', dump(self.config))

        write_fn('emodules_map', dump(self.emodules_map))
