from dtk.utils.parsers.JSON import json2dict
import os
import logging

logger = logging.getLogger(__name__)

class TaggedTemplate():
    '''
    A class for building, modifying, and writing
    input files tagged with tag (e.g. __KP), including campaign,
    demographics, and potentially even config files.
    '''

    def __init__(self, filename, contents, tag='__KP'):
        '''
        Initialize a TaggedTemplate.

        The idea here is that if you have a json file with deep nesting or a long array of events, you can plant "tags" within the file to facilitate parameter reference."  Tags are new keys adjacent to existing keys within the document.  The first part of the tagged parameter must exactly match the original parameter you wish to change.  The comes the tag, e.g. __KP.  Any string can follow the tag to uniquely identify it.

        For example, the __KP tag below allows you to set the Demographic_Coverage parameter of the second event only.

        {
            "Events" : [
                {
                    "Name": "First",
                    "Demographic_Coverage": 0.25,
                    "Range__KP_First": "<-- MARKER (this string is arbitrary)",
                    "Range" {
                        "Min": 0,
                        "Max": 1,
                    }
                },
                {
                    "Name": "Second",
                    "Demographic_Coverage__KP_Second_Coverage": "<-- MARKER (this string is arbitrary)",
                    "Demographic_Coverage": 0.25
                }
            ]
        }

        You can do some neat things with tags.
        * You can place a tagged parameter, e.g. Demographic_Coverage__KP_Second_Coverage, in several places.  The value will be set everywhere the tagged parameter is found.  For now, the whole tagged parameter must match, so Something_Else__KP_Second_Coverage would not receive the same value on set_param.
        * You can reference relateive to the tagged parameters, e.g. Range__KP_First.Min = 3
        * You don't have to use __KP, just set the tag parameter in the constructor.

        :param filename: The name of the template file.  This is not the full path to the file, just the filename.
        :param contents: The contents of the template file
        :param tag: The string that marks parameters in the file.  Note, this must begin with two underscores.
        '''

        if tag[:2] != '__':
            logger.error('Tags must start with two underscores, __.  The tag you supplied (' + tag + ') did not meet this criteria.')

        self.contents = contents
        self.filename = filename
        self.tag = tag

        self.tag_dict = self.__findKeyPaths(self.contents, self.tag)

    @classmethod
    def from_file(cls, template_filepath, tag='__KP'):
        # Read in template
        logger.info( "Reading template from file:", template_filepath )
        content = json2dict(template_filepath)

        # Get the filename and create a TaggedTemplate
        template_filename = os.path.basename(template_filepath)

        return cls(template_filename, content, tag)

    def __findKeyPaths(self, search_obj, key_fragment, partial_path=[]):
        '''
        Builds a dictionary of results from recurseKeyPaths.
        '''
        paths_found =  self.__recurseKeyPaths(search_obj, key_fragment, partial_path)

        path_dict = {}
        for path in paths_found:
            # The last part of the path should contain the key_fragment (__KP)
            # NOTE: Could change the key to be just the string following the tag here
            key = path[-1]

            # Truncate from key_fragment in k (lop off __KP_etc)
            value = path
            value[-1] = value[-1].split(key_fragment)[0]

            path_dict.setdefault(key,[]).append(value)

        return path_dict

    def __recurseKeyPaths(self, search_obj, key_fragment, partial_path=[]):
        '''
        Locates all occurrences of keys containing key_fragment in json-object 'search_obj'.
        '''
        paths_found = []

        if '.' in key_fragment:
            tmp = key_fragment.split('.')
            key_fragment = tmp[0]

        if isinstance(search_obj, dict):
            for k,v in search_obj.iteritems():
                if key_fragment in k:
                    paths_found.append( partial_path + [ k ])

            for k in search_obj.iterkeys():
                paths = self.__recurseKeyPaths(search_obj[k], key_fragment, partial_path + [k])
                for p in paths:
                    paths_found.append(p)

        elif isinstance(search_obj, list):
            for i in range(len(search_obj)):
                paths = self.__recurseKeyPaths(search_obj[i], key_fragment, partial_path + [i])
                for p in paths:
                    paths_found.append(p)

        return paths_found

    def set_params(self, params):
        """
        Call set_params to set several parameter in the tagged template file.

        :param params: A dictionary of key value pairs to be passed to set_param.
        :return: Simulation tags
        """
        sim_tags = []
        for param,value in params.iteritems():
            if self.tag in param:
                new_sim_tags = self.set_param(param, value)
                sim_tags.append( new_sim_tags )

        return sim_tags

    def set_param(self, param, value):
        """
        Call set_param to set a parameter in the tagged template file.

        This function forst expands the tagged param to a list of full addresses, and then sets the value at each address.

        :param param: The parameter to set, e.g. CAMPAIGN.My_Parameter__KP_Seeding.Max
        :param value: The value to place at expanded parameter loci.
        :return: Simulation tags
        """
        sim_tags = []
        for param in self.__expand_tags(param):
            tag = self.__set_expanded_param(param, value)
            sim_tags.append(tag)

        return sim_tags


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
            current_parameter = current_parameter[self.__cast_value(path_step)]

        # Assign the casted value to the parameter but same as for the path_step we need to cast to int if
        # its a list index and not a dictionary key
        last_step = param[-1]
        current_parameter[self.__cast_value(last_step)] = self.__cast_value(value)

        # For the tags return the non cleaned parameters so the parser can find it
        return {param_name:value}


    def __expand_tags(self, tagged_param):
        """
        Takes a tagged_param in string format and converts it to a list of parameter addresses by expanding tags from the tag dictionary.
        """

        tokens = tagged_param.split('.')

        tagged_param = tokens[0]
        if tagged_param in self.tag_dict:
            return [ expanded_tag + tokens[1:] for expanded_tag in self.tag_dict[tagged_param] ]

        return []


    def __cast_value(self,value):
        """
        Try to cas a value to float or int or string
        :param value:
        :return:
        """
        # The value is already casted
        if not isinstance(value, str) and not isinstance(value, unicode):
            return value

        # We have a string so test if only digit
        if value.isdigit():
            casted_value =  int(value)
        else:
            try:
                casted_value = float(value)
            except:
                casted_value = value

        return casted_value
