import json
import logging
import os

import utils

logger = logging.getLogger(__name__)

class SimConfigBuilder(object):
    '''
    A class for building, modifying, and writing
    required configuration files for a simulation
    '''

    def __init__(self, config={}, **kwargs):
        self.config = config
        self.update_params(kwargs, validate=True)

    @classmethod
    def from_defaults(cls, sim_type=None, **kwargs):
        if not sim_type:
            raise Exception("Instantiating SimConfigBuilder from defaults requires a sim_type argument.")
        config = dict(Simulation_Type=sim_type)  # generic base config
        return cls(config, **kwargs)

    def copy_from(self, other):
        self.__dict__ = other.__dict__.copy()

    @property
    def params(self):
        return self.config

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

    def stage_executable(self, exe_path, paths):
        staged_bin = utils.stage_file(exe_path, paths['bin_staging_root'])
        self.set_param('bin_path', staged_bin)
        return staged_bin

    def get_commandline(self, exe_path, paths):
        return utils.CommandlineGenerator(exe_path, {}, [])

    def stage_required_libraries(self, dll_path, paths):
        pass

    def dump_files(self, working_directory):
        if not os.path.exists(working_directory):
            os.makedirs(working_directory)
        def write_file(name, content):
            filename = os.path.join(working_directory, '%s.json' % name)
            with open(filename, 'w') as f:
                f.write(content)
        self.file_writer(write_file)

    def dump_files_to_string(self):
        files={}
        def update_strings(name, content):
            files[name] = content
        self.file_writer(update_strings)
        return files

    def file_writer(self, write_fn):
        dump = lambda content: json.dumps(content, sort_keys=True, indent=4)
        write_fn('config', dump(self.config))


class PythonConfigBuilder(SimConfigBuilder):

    def get_commandline(self, exe_path, paths):
        return utils.CommandlineGenerator('python', {}, [exe_path])
