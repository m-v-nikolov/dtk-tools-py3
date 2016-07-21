import json
import logging
import os

import dtk.generic.params as generic_params
import dtk.malaria.params as malaria_params
import dtk.vector.params as vector_params
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.reports.CustomReport import format as format_reports
from simtools import utils
from simtools.SimConfigBuilder import SimConfigBuilder

logger = logging.getLogger(__name__)


class DTKConfigBuilder(SimConfigBuilder):
    """
    A class for building, modifying, and writing
    required configuration files for a DTK simulation.

    There are four ways to create a DTKConfigBuilder:

    1. From a set of defaults, with the :py:func:`from_defaults` class method.
    2. From existing files, with the :py:func:`from_files` class method.
    3. From a default config/campaign by calling the constructor without arguments.
    4. From a custom config and/or campaign by calling the constructor with the ``config`` and ``campaign`` arguments.

    Arguments:
        config (dict): The config (contents of the config.json)
        campaign (dict): The campaign configuration (contents of the campaign.json)
        kwargs (dict): Additional changes to make to the config

    Attributes:
        staged_dlls (dict): Class variable holding the mapping between (type,dll name) and path
        config (dict): Holds the configuration as a dictionary
        campaign (dict): Holds the campaign as a dictionary
        demog_overlays (dict): map the demographic overlay names to content.
            Modified using the function :py:func:`add_demog_overlay`.
        input_files (dict): Dictionary map the input file names to content.
            Modified using the function :py:func:`add_input_file`.
        custom_reports (array): Array holding the custom reporters objects.
            Modified using the function :py:func:`add_reports`.
        dlls (set): Set containing a list of needed dlls for the simulations. The dlls are coming from the
            :py:func:`get_dll_path` function of the reports added by the :py:func:`add_reports`
        emodules_map (dict): Dictionary representing the ``emodules_map.json`` file.
            This dictionary is filled during the staging process happening in :py:func:`stage_required_libraries`.

    Examples:
        One can instantiate a DTKConfigBuilder with::

            config = json.load('my_config.json')
            cb = DTKConfigBuilder(config=config, campaign=None, {'Simulation_Duration':3650})

        Which will instantiate the DTKConfigBuilder with the loaded config and a default campaign and override the
        ``Simulation_Duration`` in the config.

    """

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
        """
        Build up the default parameters for the specified simulation type.

        Start from required ``GENERIC_SIM`` parameters and layer ``VECTOR_SIM``
        and also ``MALARIA_SIM`` default parameters as required.

        Configuration parameter names and values may be passed as keyword arguments,
        provided they correspond to existing default parameter names.

        P.vivax disease parameters may be approximated using ``VECTOR_SIM`` simulations
        by passing either the ``VECTOR_SIM_VIVAX_SEMITROPICAL`` or ``VECTOR_SIM_VIVAX_CHESSON``
        sim_type argument depending on the desired relapse pattern.

        Attributes:
            sim_type (string): Which simulation will be created.
                Current supported choices are:

                * MALARIA_SIM
                * VECTOR_SIM
                * VECTOR_SIM_VIVAX_SEMITROPICAL
                * VECTOR_SIM_VIVAX_CHESSON

            kwargs (dict): Additional overrides of config parameters
        """

        if not sim_type:
            raise Exception(
                "Instantiating DTKConfigBuilder from defaults requires a sim_type argument, e.g. 'MALARIA_SIM'.")

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
        """
        Build up a simulation configuration from the path to an existing
        config.json and optionally a campaign.json file on disk.

        Attributes:
            config_name (string): Path to the config file to load.
            campaign_name (string): Path to the campaign file to load.
            kwargs (dict): Additional overrides of config parameters
        """

        config = json2dict(config_name)
        campaign = json2dict(campaign_name) if campaign_name else empty_campaign

        return cls(config, campaign, **kwargs)

    @property
    def params(self):
        """
        dict: Shortcut to the ``config['parameters']``
        """
        return self.config['parameters']

    def enable(self, param):
        """
        Enable a parameter.

        Arguments:
            param (string): Parameter to enable. Note that the ``Enable_`` part of the name is automatically added.

        Examples:
            If one wants to set the ``Enable_Air_Migration`` parameter to ``1``, the way to do it would be::

                cb.enable('Air_Migration')
        """
        param = 'Enable_' + param
        self.validate_param(param)
        self.set_param(param, 1)

    def disable(self, param):
        """
        Disable a parameter.

        Arguments:
            param (string): Parameter to disable. Note that the ``Enable_`` part of the name is automatically added.

        Examples:
            If one wants to set the ``Enable_Demographics_Birth`` parameter to ``0``, the way to do it would be::

                cb.disable('Demographics_Birth')
        """
        param = 'Enable_' + param
        self.validate_param(param)
        self.set_param(param, 0)

    def add_event(self, event):
        """
        Add an event to the campaign held by the config builder.

        Args:
            event (dict): The dictionary holding the event to be added.

        Examples:
            To add an event to an existing config builder, one can do::

                event = {
                    "Event_Coordinator_Config": {
                        "Intervention_Config": {
                            [...]
                        },
                        "Number_Repetitions": 1,
                        "class": "StandardInterventionDistributionEventCoordinator"
                    },
                    "Event_Name": "Input EIR intervention",
                    [...]
                    }

                cb.add_event(event)

        """
        self.campaign["Events"].append(event)

    def clear_events(self):
        """
        Removes all events from the campaign
        """
        self.campaign["Events"] = []

    def add_reports(self, *reports):
        """
        Add the reports to the ``custom_reports`` dictionary. Also extract the required dlls and add them to the
        ``dlls`` set.

        Args:
            reports (list): List of reports to add to the config builder
        """
        for r in reports:
            self.custom_reports.append(r)
            self.dlls.add(r.get_dll_path())

    def add_input_file(self, name, content):
        """
        Add input file to the simulation.
        The file can be of any type.

        Args:
            name (string): Name of the file. Will be used when the file is written to the simulation directory.
            content (string): Contents of the file.

        Examples:
            Usage for this function could be::

                my_txt = open('test.txt', 'r')
                cb.add_input_file('test.txt',my_txt.read())

        """
        if name in self.input_files:
            logger.warn('Already have input file named %s, replacing previous input file.' % name)
        self.input_files[name] = content

    def append_overlay(self, demog_file):
        """
        Append a demographic overlay at the end of the ``Demographics_Filenames`` array.

        Args:
            demog_file (string): The demographic file name to append to the array.

        """
        self.config['parameters']['Demographics_Filenames'].append(demog_file)

    def add_demog_overlay(self, name, content):
        """
        Add a demographic overlay to the simulation.

        Args:
            name (string): Name of the demographic overlay
            content (string): Content of the file

        """
        if name in self.demog_overlays:
            raise Exception('Already have demographics overlay named %s' % name)
        self.demog_overlays[name] = content

    def get_commandline(self, exe_path, paths):
        """
        Get the complete command line to run the simulation.

        Args:
            exe_path (string): The path to the model executable
            paths (dict): Dictionary containing the setup and allowing this function to retrieve the ``input_root`` and ``python_path``

        Returns:
            The :py:class:`CommandlineGenerator` object created with the correct paths

        """
        eradication_options = {'--config': 'config.json', '--input-path': paths['input_root']}

        if 'python_path' in paths and paths['python_path'] != '':
            eradication_options['--python-script-path'] = paths['python_path']

        return utils.CommandlineGenerator(exe_path, eradication_options, [])

    def stage_required_libraries(self, dll_path, staging_root, assets_service=False):
        """
        Stage the required DLLs.

        This function will work differently depending on the use of the assets service or not.
        If the assets service is used, the function will simply create the path for the dll and not copy the file itself.
        If the assets service is not used, the function will call the :py:func:`stage_file` function and store
        the returned path.

        For each dll to stage, the ``staged_dlls`` dictionary is updated with the path to the dll mapped to its
        type and name and the ``emodules_map`` dictionary is also updated accordingly.

        Args:
            dll_path (string): The path where the dll to be staged are
            staging_root (string): The staging dll path
            assets_service (bool): Are we using the assets service?

        """
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
                    staged_dll = os.path.join(staging_root, dll_type, dll_name)
                # caching to avoid repeat md5 and os calls
                self.staged_dlls[(dll_type, dll_name)] = staged_dll

            # Add the dll to the emodules_map
            self.emodules_map[dll_type].append(staged_dll)

    def file_writer(self, write_fn):
        """
        Dump all the files needed for the simulation in the simulation directory.
        This includes:

        * The campaign file
        * The custom reporters file
        * The different demographic overlays
        * The other input files (``input_files`` dictionary)
        * The config file
        * The emodules_map file

        Args:
            write_fn: The function that will write the files. This function needs to take a file name and a content.

        Examples:
            For example, in the :py:class:`SimConfigBuilder` class, the :py:func:`dump_files` is defining the `write_fn`
            like::

                def write_file(name, content):
                    filename = os.path.join(working_directory, '%s.json' % name)
                    with open(filename, 'w') as f:
                        f.write(content)
        """


        dump = lambda content: json.dumps(content, sort_keys=True, indent=4)

        write_fn(self.config['parameters']['Campaign_Filename'], dump(self.campaign))

        if self.custom_reports:
            self.set_param('Custom_Reports_Filename', 'custom_reports.json')
            write_fn('custom_reports.json', dump(format_reports(self.custom_reports)))

        for name, content in self.demog_overlays.items():
            self.append_overlay('%s.json' % name)
            write_fn(name, dump(content))

        for name, content in self.input_files.items():
            write_fn(name, dump(content))

        write_fn('config.json', dump(self.config))

        write_fn('emodules_map.json', dump(self.emodules_map))
