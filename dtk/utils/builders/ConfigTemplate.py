from dtk.utils.parsers.JSON import json2dict
import os
import sys
import re   # for splitting on multiple characters, [ and ]
import logging

import dtk.utils.builders.ITemplate as ITemplate

logger = logging.getLogger(__name__)

class ConfigTemplate(ITemplate.BaseTemplate):
    '''
    A class for building, modifying, and writing config.json DTK input files.
    '''

    def __init__(self, filename, contents):
        '''
        Initialize a ConfigTemplate.
        :param filename: The name of the template file.  This is not the full path to the file, just the filename.
        :param contents: The contents of the template file
        '''

        self.contents = contents['parameters']
        self.filename = filename
        self.known_params = {}

    @classmethod
    def from_file(cls, template_filepath):
        # Read in template
        logger.info( "Reading config template from file:", template_filepath )
        contents = json2dict(template_filepath)

        # Get the filename and create a TaggedTemplate
        template_filename = os.path.basename(template_filepath)

        return cls(template_filename, contents)

    # ITemplate functions follow
    def get_filename(self):
        return self.filename

    def get_contents(self):
        return {"parameters": self.contents}

    def is_consumed_by_template(self, param):
        if param in self.known_params:
            return self.known_params[param]

        # First time looking for this parameter.  Try to find it and add to list of known parameters
        try:
            value = self.get_param(param)
            is_param = True
        except (KeyError, TypeError, IndexError) as e:
            is_param = False

        self.known_params[param] = is_param
        return is_param

    def set_params(self, params):
        """
        Call set_params to set several parameter in the config file.

        :param params: A dictionary of key value pairs to be passed to set_param.
        :return: Simulation tags
        """
        sim_tags = []
        for param,value in params.iteritems():
            new_sim_tags = self.__set_param(param, value)
            sim_tags.append( new_sim_tags )

        return sim_tags

    def __set_param(self, param, value):
        """
        Call __set_param to set a parameter in the tagged template file.

        :param param: The parameter to set, e.g. Base_Infectivity
        :param value: The value to place at expanded parameter loci.
        :return: Simulation tags
        """

        path_steps = param.split('.')
        current_parameter = self.contents

        for path_step in path_steps[:-1]:
            if '[' in path_step:
                subpaths = path_step.split('[')
                assert( subpaths[1][-1] == ']' )
                path_step = subpaths[0]
                index = int(float(subpaths[1][:-1]))
                current_parameter = current_parameter[self.cast_value(path_step)]
                current_parameter = current_parameter[index]
            else:
                # If the step is a number, we are in a list, we need to cast the step to int
                current_parameter = current_parameter[self.cast_value(path_step)]

        current_parameter[path_steps[-1]] = self.cast_value(value)

        return {param: value}


    def set_params_and_modify_cb(self, params, cb):
         self.set_params(params)
         cb.config = self.get_contents()

    def __set_expanded_param(self, param, value):
        """
        Sets the parameter value in the template.

        :param param: The parameter address to set in a list form, e.g. ['CAMPAIGN', 'Events', 3, 'My_Parameter', 'Max'].
        :param value: The value to set at address param.
        :return: The parameter name and value in a format compatible with simulation tagging.
        """
        param_name = '.'.join( str(p) for p in param)
        logger.info( "[%s] Setting parameter %s = %s." % (self.filename, param_name, str(value)) )

        current_parameter = self.contents

        for path_step in param[:-1]:
            # If the step is a number, we are in a list, we need to cast the step to int
            current_parameter = current_parameter[self.cast_value(path_step)]

        # Assign the casted value to the parameter but same as for the path_step we need to cast to int if
        # its a list index and not a dictionary key
        last_step = param[-1]
        current_parameter[self.cast_value(last_step)] = self.cast_value(value)

        # For the tags return the non cleaned parameters so the parser can find it
        return {param_name:value}


