import json
import logging
import os

import utils

logger = logging.getLogger(__name__)

class ConfigurationJson(object):
    '''
    A class for building, modifying, and writing
    required configuration files for a simulation
    '''

    def __init__(self, contents={}, filename='config', **kwargs):
        self.contents = contents['parameters']
        self._filename = filename
        self.update_params(kwargs, validate=True)

    def copy_from(self, other):
        self.__dict__ = other.__dict__.copy()

    @property
    def filename(self):
        return self._filename

    @property
    def params(self):
        return self.contents

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
        write_fn( self.filename.replace(".json",""), dump(self.contents))
