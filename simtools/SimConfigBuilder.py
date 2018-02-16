import logging
import os
from abc import abstractmethod, ABCMeta

from simtools.AssetManager.SimulationAssets import SimulationAssets
from simtools.Utilities.COMPSUtilities import stage_file
from simtools.Utilities.General import CommandlineGenerator

logger = logging.getLogger(__name__)


class SimConfigBuilder(metaclass=ABCMeta):
    """
    A class for building, modifying, and writing
    required configuration files for a simulation
    """

    def __init__(self, config=None, **kwargs):
        self.config = config or {}
        self.assets = SimulationAssets()
        self.ignore_missing = False
        self.human_readability = True
        if kwargs: self.update_params(kwargs, validate=True)

    def copy_from(self, other):
        self.__dict__ = other.__dict__.copy()

    @property
    def params(self):
        return self.config

    @property
    def exe_name(self):
        return self.assets.exe_name

    def update_params(self, params, validate=False):
        if not validate:
            self.params.update(params)
        else:
            for k, v in params.items():
                self.validate_param(k)
                logger.debug('Overriding: %s = %s' % (k, v))
                self.set_param(k, v)
        return params  # for ModBuilder metadata

    def set_param(self, param, value):
        self.params[param] = value
        return {param: value}  # for ModBuilder metadata

    def get_param(self, param, default=None):
        return self.params.get(param, default)

    def validate_param(self, param):
        if param not in self.params:
            raise Exception('No parameter named %s' % param)
        return True

    def stage_executable(self, exe_path, bin_staging_root):
        staged_bin = stage_file(exe_path, bin_staging_root)
        self.set_param('bin_path', staged_bin)
        return staged_bin

    @abstractmethod
    def get_commandline(self):
        return CommandlineGenerator('executable', [], {})

    def dump_files(self, working_directory):
        if not os.path.exists(working_directory):
            os.makedirs(working_directory)

        def write_file(name, content):
            filename = os.path.join(working_directory, '%s' % name)
            with open(filename, 'w') as f:
                f.write(content)

        self.file_writer(write_file)

    def dump_files_to_string(self):
        files = {}

        def update_strings(name, content):
            files[name] = content

        self.file_writer(update_strings)
        return files

    @abstractmethod
    def file_writer(self, write_fn):
        pass

    @property
    def experiment_files(self):
        return self.assets.experiment_files

    def get_assets(self):
        self.assets.create_collections(self)
        return self.assets

    def set_experiment_executable(self, path):
        self.assets.exe_path = os.path.abspath(path)

    def set_input_files_root(self, path):
        self.assets.input_root = os.path.abspath(path)

    def set_dll_root(self, path):
        self.assets.dll_root = os.path.abspath(path)

    def set_python_path(self, path):
        self.assets.python_path = os.path.abspath(path)

    def set_input_collection(self, collection):
        self.assets.set_base_collection(SimulationAssets.INPUT, collection)

    def set_python_collection(self, collection):
        self.assets.set_base_collection(SimulationAssets.PYTHON, collection)

    def set_dll_collection(self, collection):
        self.assets.set_base_collection(SimulationAssets.DLL, collection)

    def set_exe_collection(self, collection):
        self.assets.set_base_collection(SimulationAssets.EXE, collection)

    def set_collection_id(self, collection):
        self.assets.set_base_collection(SimulationAssets.MASTER, collection)

    @abstractmethod
    def get_dll_paths_for_asset_manager(self):
        return []

    @abstractmethod
    def get_input_file_paths(self):
        return []

