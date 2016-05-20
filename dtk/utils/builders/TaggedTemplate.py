import json
import logging
import os

logger = logging.getLogger(__name__)

class TaggedTemplate():
    '''
    A class for building, modifying, and writing
    input files tagged with tag (e.g. __KP), including campaign
    and demographics files.
    TODO: MORE
    '''

    def __init__(self, filename, contents, tag='__KP'):
        self.contents = contents
        self.filename = filename
        self.tag = tag

        self.tag_dict = self.findKeyPaths(self.contents, self.tag)

    def findKeyPaths(self, search_obj, key_fragment, partial_path=[]):
        paths_found =  self.recurseKeyPaths(search_obj, key_fragment, partial_path)

        path_dict = {}
        for path in paths_found:
            key = path[-1]
            value = path

            # Truncate from key_fragment in k
            value[-1] = value[-1].split(key_fragment)[0]

            path_dict.setdefault(key,[]).append(value)

        return path_dict

    def recurseKeyPaths(self, search_obj, key_fragment, partial_path=[]):
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
                paths = self.recurseKeyPaths(search_obj[k], key_fragment, partial_path + [k])
                for p in paths:
                    paths_found.append(p)

        elif isinstance(search_obj, list):
            for i in range(len(search_obj)):
                paths = self.recurseKeyPaths(search_obj[i], key_fragment, partial_path + [i])
                for p in paths:
                    paths_found.append(p)

        return paths_found

    def expand_tags(self, tagged_param):
        # Surely a better way to do this!
        prefix = []
        postfix = []

        tokens = tagged_param.split('.')

        found = False
        for tok in tokens:
            if not found:
                if self.tag in tok:
                    tag = tok
                    found = True
                else:
                    prefix.append(tok)
            else:
                postfix.append(tok)

        if not found or tag not in self.tag_dict:
            return []

        return [prefix + p + postfix for p in self.tag_dict[tag]]


    def set_param(self, param, value):
        tags = []
        for param in self.expand_tags(param):
            tag = self.set_expanded_param(param, value)
            tags.append(tag)

        return tags

    def set_expanded_param(self, param, value):
        param_name = '.'.join( str(p) for p in param)
        print "[%s] Setting parameter %s = %s." % (self.filename, param_name, str(value))

        current_parameter = self.contents

        for path_step in param[1:-1]:
            # If the step is a number, we are in a list, we need to cast the step to int
            current_parameter = current_parameter[self.cast_value(path_step)]

        # Assign the casted value to the parameter but same as for the path_step we need to cast to int if
        # its a list index and not a dictionary key
        last_step = param[-1]
        current_parameter[self.cast_value(last_step)] = self.cast_value(value)

        # For the tags return the non cleaned parameters so the parser can find it
        return {param_name:value}


    def cast_value(self,value):
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
