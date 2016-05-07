from simtools.ModBuilder import ModBuilder
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.builders.TabularConfigBuilder import TabularConfigBuilder


# QUESTIONABLE:
from COMPS_Worker_Plugin import Builder_Plugin_Helper

import json, copy, os
from collections import OrderedDict, namedtuple

from COMPS_Worker_Plugin import Builder_Plugin_Helper
from COMPS_Worker_Plugin.Builder_JSON_Utilities import setParameter
from COMPS_Worker_Plugin.Builder_JSON_Utilities import findKeyPaths
from COMPS_Worker_Plugin.COMPS_Entities import *



# TODO: Match DEMOGRAPHICS KP parameters to individual files.  Make sure every KP entry can be found in at least one file
# TODO: Be more careful about using findKeyPaths.  Should precipitate from the above mapping of paramters to files

class TabularModBuilder(ModBuilder):
    def __init__(self, plugin_info_json):
        self.plugin_info_json = json2dict(plugin_info_json)
        assert( 'Dynamic_Parameters' in self.plugin_info_json )

        self.dynamic_parameters = self.plugin_info_json['Dynamic_Parameters']
        self.run_number = self.dynamic_parameters['Run_Number']
        self.header = self.dynamic_parameters['Header']
        self.table = self.dynamic_parameters['Table']

        print "Found a table with",len(self.table),"rows of dynamic parameters."
        self.mod_generator = (
            self.set_mods(
                [
                    self.ModFn( TabularConfigBuilder.map_and_update_params_for_all_templates, dict(zip(self.header, row)) )
                ]
            ) for row in self.table
        )

