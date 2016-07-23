import abc
import os
import logging

import re
from dtk.utils.parsers.JSON import json2dict

logger = logging.getLogger(__name__)


class ITemplate(object):
    """
    Abstract class for working with templates.
    """

    __metaclass__ = abc.ABCMeta

    @abc.abstractmethod
    def get_filename(self):
        """
        Gets the file name.
        :return: The filename
        """

    @abc.abstractmethod
    def get_contents(self):
        """
        Returns the file contents, potentially modified.
        :return: file contents
        """

    @abc.abstractmethod
    def has_param(self, parameter):
        """Checks if key is used by the template
        :param key: The key to look for
        :return: Boolean.
        """

    @abc.abstractmethod
    def set_params(self, param_dict):
        """
        Sets parameters.
        :param param_dict: A dictionary of key value pairs to set.  Keys not used by the template will be ignored.
        :return: tag dictionary of key value pairs that were set.
        """

    @abc.abstractmethod
    def set_param(self, param, value):
        """
        Sets one parameter
        :param param: A parameter
        :param value: The value
        :return: a dictionary with a single key:value pair
        """

    @abc.abstractmethod
    def get_param(self, param):
        """
        Gets a parameter value.  The return type is a dictionary because some tagged parameters can have multiple addresses, and therefore multiple values.
        :param param: The parameter, may contain '.' and numeric indices, '[0]',  e.g. Events[3].Start_Day
        :return: A dictionary of key value pairs
        """

    @abc.abstractmethod
    def set_params_and_modify_cb(self, params, cb):
        """
        Sets parameters and potentially also modifies a config builder instance
        :param params: A dictionary of parameters to set
        :param cb: An instance of a DTKConfigBuilder
        :return: Simulation tags
        """


class BaseTemplate(ITemplate):
    def __init__(self, filename, contents):
        """
        Initialize a BaseTemplate.
        :param filename: The name of the template file.  This is not the full path to the file, just the filename.
        :param contents: The contents of the template file
        """

        self.contents = contents
        self.filename = filename
        self.known_params = {}

    @classmethod
    def from_file(cls, template_filepath):
        """
        Initialize a BaseTemplate from a file path.
        :param template_file: Path to the file on disk.
        """
        # Read in template
        logger.info("Reading config template from file: %s" % template_filepath)
        contents = json2dict(template_filepath)

        # Get the filename and create a ConfigTemplate
        template_filename = os.path.basename(template_filepath)

        return cls(template_filename, contents)

    def get_filename(self):
        return self.filename

    def get_contents(self):
        return self.contents

    def has_param(self, param):
        """
        Boolean to determine if this template can set param.
        :return: Boolean
        """
        if param in self.known_params:
            return self.known_params[param]

        # First time looking for this parameter.  Try to find it and add to list of known parameters
        try:
            self.get_param(param)
            is_param = True
        except (KeyError, TypeError, IndexError) as e:
            is_param = False

        self.known_params[param] = is_param
        return is_param

    def get_param(self, param):
        """
        Gets a parameter value.  The return type is a dictionary because some tagged parameters can have multiple addresses, and therefore multiple values.
        :param param: The parameter, may contain '.' and numeric indices, '[0]',  e.g. Events[3].Start_Day
        :return: A tuple of (value, param)
        """
        contents, key = self.get_param_handle(param)

        return param, contents[key]

    def set_param(self, param, value):
        """
        Call set_param to set a parameter in the template file.  List indices can be provided via brackets or dots, e.g.
        * Events[3].Whatever
        * Events.3.Whatever

        :param param: The parameter to set, e.g. Base_Infectivity
        :param value: The value to place at expanded parameter loci.
        :return: Simulation tags
        """
        contents, key = self.get_param_handle(param)
        contents[key] = self.cast_value(value)

        return {"[" + self.get_filename() + "] " + param: value}

    def set_params(self, params):
        """
        Call set_params to set several parameter in the config file.

        :param params: A dictionary of key value pairs to be passed to set_param.
        :return: Simulation tags
        """
        sim_tags = {}
        for param, value in params.iteritems():
            if self.has_param(param):
                new_sim_tags = self.set_param(param, value)
                sim_tags.update(new_sim_tags)

        return sim_tags

    def get_param_handle(self,path):
        """
        Get the parameter handle.
        This function basically returns the dictionary pointer and parameter depending on the path passed.

        Examples:
            contents, key = self.get_param_handle('Events[0].class')
            print contents[key] # prints CampaignEventByYear
            contents[key] = 'test'
            # Now contents['Events'][0]['class'] is set to 'test'

        Args:
            path: path to the parameter

        Returns:
            contents: the dictionary 'pointer'
            key: the key corresponding to the parameter

        """
        path_steps = path.split('.')
        contents = self.contents
        pattern = '(\w+)\[*(\d*)\]*'

        # Traverse until we reach the last parameter
        for path_step_index in range(len(path_steps) - 1):
            path_step = path_steps[path_step_index]
            # Match either something or something[digit]
            groups = re.match(pattern, path_step).groups()
            # Always traverse the first group
            contents = contents[self.cast_value(groups[0])]
            # And traverse the rest if it exists
            contents = contents[self.cast_value(groups[1])] if groups[1] else contents

        # Handle the case where we have a path like finishing by an indexed params (example: Events[1])
        groups = re.match(pattern, path_steps[-1]).groups()
        if not groups[1]:
            return contents, self.cast_value(path_steps[-1])
        return contents[self.cast_value(groups[0])], self.cast_value(groups[1])

    def cast_value(self, value):
        """
        Try to cas a value to float or int or string
        :param value: The value to cast.
        :return: The casted value.
        """
        # The value is already casted
        if not isinstance(value, str) and not isinstance(value, unicode):
            return value

        # We have a string so test if only digit
        if value.isdigit():
            casted_value = int(value)
        else:
            try:
                casted_value = float(value)
            except:
                casted_value = value

        return casted_value

    def set_params_and_modify_cb(self, params, cb):
        pass