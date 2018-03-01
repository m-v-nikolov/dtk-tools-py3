import json
import os

from simtools.SimConfigBuilder import SimConfigBuilder
from simtools.Utilities.Encoding import NumpyEncoder
from models.cms.core.CMS_Object import *
from models.cms.core.CMS_Parser import CMSParser


class CMSConfigBuilder(SimConfigBuilder):

    def __init__(self, model, config=None, start_model_name=None):
        super(CMSConfigBuilder, self).__init__(config)
        self.model = model
        self.start_model_name = start_model_name
        self.species = {}
        self.param = {}
        self.func = {}
        self.bool = {}
        self.observe = []
        self.reaction = []
        self.time_event = []
        self.state_event = []

    def set_config_param(self, param, value):
        self.config[param] = value

    def get_config_param(self, param):
        return self.config[param] if param in self.config else None

    def get_commandline(self):
        """
        Get the complete command line to run the simulations of this experiment.
        Returns:
            The :py:class:`CommandlineGenerator` object created with the correct paths

        """
        from simtools.Utilities.General import CommandlineGenerator
        from simtools.SetupParser import SetupParser

        cms_options = {'-config': 'config.json', '-model': 'model.emodl'}

        if SetupParser.get('type') == 'LOCAL':
            exe_path = self.assets.exe_path
        else:
            exe_path = os.path.join('Assets', self.exe_name)

        return CommandlineGenerator(exe_path, cms_options, [])

    @classmethod
    def from_files(cls, model_file, config_file=None, **kwargs):
        """
        Build up a simulation configuration from the path to an existing
        cfg and optionally a campaign.json file on disk.

        Attributes:
            config_file (string): Path to the config file to load.
            model_file (string): Path to the model file to load.
            kwargs (dict): Additional overrides of config parameters
        """
        # Normalize the paths
        model_file = os.path.abspath(os.path.normpath(model_file))
        config_file = os.path.abspath(os.path.normpath(config_file)) if config_file else config_file

        # Read the config
        if config_file:
            config = json.load(open(config_file, 'r'))
        else:
            config = {}

        # Do the overrides
        config.update(**kwargs)

        # first, create CMSBuilder with empty model
        cb = cls(None, config)

        # then parse model file
        CMSParser.parse_model_from_file(model_file, cb)
        return cb

    @classmethod
    def from_defaults(cls):
        # return cb with empty model and config
        return cls(None, None, 'my_cms_model')

    def file_writer(self, write_fn):
        """
        Dump all the files needed for the simulation in the simulation directory.
        This includes:

        * The model file
        * The config file

        Args:
            write_fn: The function that will write the files. This function needs to take a file name and a content.
        """
        # Handle the config
        if self.human_readability:
            config = json.dumps(self.config, sort_keys=True, indent=3, cls=NumpyEncoder).strip('"')
        else:
            config = json.dumps(self.config, sort_keys=True, cls=NumpyEncoder).strip('"')

        write_fn('config.json', config)

        # And now the model
        self.model = self.to_model()
        write_fn('model.emodl', self.model)

    def get_dll_paths_for_asset_manager(self):
        from simtools.AssetManager.FileList import FileList
        fl = FileList(root=self.assets.dll_root, recursive=True)
        return [f.absolute_path for f in fl.files if f.file_name != self.assets.exe_path]

    def get_input_file_paths(self):
        return []


    #######################
    # code to build emodl
    #######################

    @staticmethod
    def clean_value(value):
        if isinstance(value, float):
            return "{:.10f}".format(value).rstrip('0')

        return value

    @staticmethod
    def clean_in_out(value):
        return "({})".format(str(value).strip(')( '))

    @staticmethod
    def trim_value(value):
        return value.strip() if value else value

    def add_species(self, name, value=None):
        value = self.trim_value(value)
        self.species[name] = Species(name, value)

    def set_species(self, name, value=None):
        self.species[name] = Species(name, value)

    def get_species(self, name):
        return self.species[name].value

    def add_time_event(self, name, iteration=None, *pair_list):
        self.time_event.append(TimeEvent(name, iteration, *pair_list))

    def add_state_event(self, name, *pair_list):
        self.state_event.append(StateEvent(name, *pair_list))

    def add_reaction(self, name, input, output, func):
        input = self.clean_in_out(input)
        output = self.clean_in_out(output)
        func = self.trim_value(func)
        self.reaction.append(Reaction(name, input, output, func))

    def add_param(self, name, value):
        value = self.trim_value(value)
        value = self.clean_value(value)
        self.param[name] = Param(name, value)

    def set_param(self, name, value):
        value = self.clean_value(value)
        self.param[name] = Param(name, value)
        return {name:value}

    def get_param(self, name, default=None):
        return self.param[name].value if name in self.param else default

    def add_func(self, name, func):
        func = self.trim_value(func)
        self.func[name] = Func(name, func)

    def set_func(self, name, func):
        self.func[name] = Func(name, func)

    def get_func(self, name):
        return self.func[name].func

    def add_observe(self, label, func):
        func = self.trim_value(func)
        self.observe.append(Observe(label, func))

    def add_bool(self, name, expr):
        expr = self.trim_value(expr)
        self.bool[name] = Bool(name, expr)

    def set_bool(self, name, expr):
        self.bool[name] = Bool(name, expr)

    def get_bool(self, name):
        return self.bool[name].expr

    def to_model(self):
        out_list = []

        def add_to_display(objs):
            if objs:
                out_list.append('\n')
                if isinstance(objs, dict):
                    out_list.extend(objs.values())
                elif isinstance(objs, list):
                    out_list.extend(objs)

        out_list.append('(import (rnrs) (emodl cmslib))')
        out_list.append('(start-model "{}")'.format(self.start_model_name))

        add_to_display(self.species)

        add_to_display(self.param)

        add_to_display(self.func)

        add_to_display(self.bool)

        add_to_display(self.reaction)

        add_to_display(self.observe)

        add_to_display(self.state_event)

        add_to_display(self.time_event)

        out_list.append('\n')
        out_list.append('(end-model)')

        out_list = [str(i) if i != '\n' else i for i in out_list]
        return '\n'.join(out_list)

    def save_to_file(self, filename):
        f = open('{}.emodl'.format(filename), 'w')
        f.write(self.to_model())
        f.close()


