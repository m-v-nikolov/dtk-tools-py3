import json
import logging
import os

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

    def get_contents(self):
        return {'parameters': self.contents}

    def append_demographics_overlay(self, filename):
        self.contents['Demographics_Filenames'].append(filename)

    def reset_demographic_overlays(self):
        self.contents['Demographics_Filenames'] = []
