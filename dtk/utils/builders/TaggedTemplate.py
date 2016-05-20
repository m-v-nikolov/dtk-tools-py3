import logging

logger = logging.getLogger(__name__)

class TaggedTemplate():
    '''
    A class for building, modifying, and writing
    input files tagged with tag (e.g. __KP), including campaign
    and demographics files.
    '''

    def __init__(self, filename, contents, tag='__KP'):
        self.contents = contents
        self.filename = filename
        self.tag = tag

        self.tag_dict = self.__findKeyPaths(self.contents, self.tag)

    def __findKeyPaths(self, search_obj, key_fragment, partial_path=[]):
        '''
        Builds a dictionary of results from recurseKeyPaths.
        '''
        paths_found =  self.__recurseKeyPaths(search_obj, key_fragment, partial_path)

        path_dict = {}
        for path in paths_found:
            key = path[-1]
            value = path

            # Truncate from key_fragment in k
            value[-1] = value[-1].split(key_fragment)[0]

            path_dict.setdefault(key,[]).append(value)

        return path_dict

    def __recurseKeyPaths(self, search_obj, key_fragment, partial_path=[]):
        '''
        Locates all occurrences of keys containing key_fragment in json-object 'search_obj'
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


    def __expand_tags(self, tagged_param):
        """
        Takes a tagged_param in string format and converts it to a list of parameter addresses by expanding tags from the tag dictionary.
        """

        tokens = tagged_param.split('.')

        tagged_param = tokens[0]
        if tagged_param in self.tag_dict:
            return [ expanded_tag + tokens[1:] for expanded_tag in self.tag_dict[tagged_param] ]

        return []


    def set_param(self, param, value):
        """
        Call set_param to set a parameter in the tagged template file.

        This function forst expands the tagged param to a list of full addresses, and then sets the value at each address.

        :param param: The parameter to set, e.g. CAMPAIGN.My_Parameter__KP_Seeding.Max
        :param value: The value to place at expanded parameter loci.
        """
        tags = []
        for param in self.__expand_tags(param):
            tag = self.__set_expanded_param(param, value)
            tags.append(tag)

        return tags

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
