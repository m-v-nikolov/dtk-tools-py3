import json
import logging
import os

from COMPS_Worker_Plugin.Builder_JSON_Utilities import setParameter
from COMPS_Worker_Plugin.Builder_JSON_Utilities import findKeyPaths

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

        self.build_KP_map()

    def build_KP_map(self):
        path_els = keypath.split('.')

        idx = path_els[0].find('__KP')

        if idx != -1:
# do we care about checking everything after __KP is an int?
            len_kp_suffix = len(path_els[0]) - idx

            if kp_dict is not None and path_els[0] in kp_dict:
                paths = kp_dict[path_els[0]]
            else:
                paths = findKeyPaths(obj, path_els[0])

        for p in paths:
            p[-1] = p[-1][ : -1 * len_kp_suffix ]

        if kp_dict is not None:
            kp_dict[path_els[0]] = paths

        if len(path_els) > 1:
            paths = [ p + path_els[1:] for p in paths ]

        if len(paths) == 0:
            raise RuntimeError('Couldn\'t find path matching \'' + keypath + '\'') 

def findKeyPaths(search_obj, key, partial_path=[]):
'''
Locates all occurrences of key 'key' in json-object 'search_obj'
'''
    paths_found = []

    if '.' in key:
        tmp = key.split('.')
        key = tmp[0]

    if isinstance(search_obj, dict):
        if key in search_obj:
            paths_found.append( partial_path + [ key ])

        for k in search_obj.iterkeys():
            paths = findKeyPaths(search_obj[k], key, partial_path + [k])
            for p in paths:
                paths_found.append(p)

    elif isinstance(search_obj, list):
        for i in range(len(search_obj)):
            paths = findKeyPaths(search_obj[i], key, partial_path + [i])
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
