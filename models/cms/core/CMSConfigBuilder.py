import json
import os

from simtools.SimConfigBuilder import SimConfigBuilder
from simtools.Utilities.Encoding import NumpyEncoder


class CMSConfigBuilder(SimConfigBuilder):

    def __init__(self, model, config=None):
        super(CMSConfigBuilder, self).__init__(config)
        self.model = model

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

        eradication_options = {'-config': 'config.json', '-model': 'model.emodl'}

        if SetupParser.get('type') == 'LOCAL':
            exe_path = self.assets.exe_path
        else:
            exe_path = os.path.join('Assets', os.path.basename(self.assets.exe_path or 'compartments.exe'))

        return CommandlineGenerator(exe_path, eradication_options, [])

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

        # Read the model file
        model = open(model_file, 'r').read()

        # Read the config
        if config_file:
            config = json.load(open(config_file, 'r'))
        else:
            config = {}

        # Do the overrides
        config.update(**kwargs)

        return cls(model, config)

    @classmethod
    def from_defaults(cls):
        raise NotImplemented("from_defaults is not yet implemented. Please use the from_files method instead.")

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
        write_fn('model.emodl', self.model)

    def get_dll_paths_for_asset_manager(self):
        from simtools.AssetManager.FileList import FileList
        fl = FileList(root=self.assets.dll_root, recursive=True)
        return [f.absolute_path for f in fl.files if f.file_name != self.assets.exe_path]

    def get_input_file_paths(self):
        return []


