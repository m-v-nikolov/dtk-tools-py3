import json
import logging
import os

#from COMPS_Worker_Plugin.Builder_JSON_Utilities import setParameter
#from COMPS_Worker_Plugin.Builder_JSON_Utilities import findKeyPaths

logger = logging.getLogger(__name__)

class KPTaggedTemplate():
    '''
    A class for building, modifying, and writing
    input files tagged with __KP, including campaign
    and demographics files.
    TODO: MORE
    '''

    def __init__(self, filename, contents):
        self.contents = contents
        self.filename = filename

        self.KP_dict = self.findKeyPaths(self.contents, '__KP')

    def findKeyPaths(self, search_obj, key_fragment, partial_path=[]):

        paths_found =  self.recurseKeyPaths(search_obj, key_fragment, partial_path)

        path_dict = {}
        for path in paths_found:
            #print path
            key = path[-1]
            value = path
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
            #if key in search_obj:
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


    def update_params(self, params, validate=False):
        if not validate:
            self.params.update(params)  # DJK NOTE: ModBuilder metadata only when validate=True
        else:
            for k, v in params.items():
                self.validate_param(k)
                logger.debug('Overriding: %s = %s' % (k, v))
                self.set_param(k, v)
        return params  # for ModBuilder metadata


    def set_param(self, param, value):
        print "[",self.filename,"] SET_PARAM %s=%f:" % (param, value)
        return zip(*params)  # for ModBuilder metadata

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
