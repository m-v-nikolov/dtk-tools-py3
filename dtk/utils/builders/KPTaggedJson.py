import json
import logging
import os

import utils

from dtk.utils.builders.ConfigurationJson import ConfigurationJson

logger = logging.getLogger(__name__)

class KPTaggedJson(ConfigurationJson):
    '''
    A class for building, modifying, and writing
    input files tagged with __KP, including campaign
    and demographics files.
    TODO: MORE
    '''

    def __init__(self, contents={}, filename='campaign', **kwargs):
        self.contents = contents
        self._filename = filename
        if kwargs:
            self.update_params(kwargs, validate=True)

    def update_params(self, params, validate=False):
        print "[",self.filename,"] UPDATE_PARAMS with params:", params
        #if not validate:
        #    self.params.update(params)
        #else:
        #    for k, v in params.items():
        #        self.validate_param(k)
        #        logger.debug('Overriding: %s = %s' % (k, v))
        #        self.set_param(k, v)
        #return params  # for ModBuilder metadata

    def set_param(self, param, value):
        print "[",self.filename,"] SET_PARAM with params:", param
        #self.params[param] = value
        return {param: value}  # for ModBuilder metadata

    def get_param(self, param, default=None):
        print "[",self.filename,"] GET_PARAM with params:", param
        return 0
        #return self.params.get(param, default)

    def validate_param(self, param):
        print "[",self.filename,"] VALIDATE_PARAM with params:", param
        #if param not in self.params:
        #    raise Exception('No parameter named %s' % param)
        return True

    def get_contents(self):
        return self.contents
