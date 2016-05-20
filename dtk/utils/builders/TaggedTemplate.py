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

    def expand_tags(self, tagged_params):
        expanded_tags = []
        for tagged_param in tagged_params:
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

            #if not found:
            #    raise RuntimeWarning('['+tagged_param+']: Could not find tag ' + self.tag)

            #if tag not in self.tag_dict:
            #    raise RuntimeWarning('['+tag+']: Could not find corresponding tag in file ' + self.filename)

            if found and tag in self.tag_dict:
                full_param_path = [prefix + p + postfix for p in self.tag_dict[tag]]
                #print tag,'-->', self.tag_dict[tag],'-->',full_param_path
                expanded_tags.append( full_param_path )

        return expanded_tags
