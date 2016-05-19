import copy
import warnings
import os

from simtools.ModBuilder import ModBuilder
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.builders.TaggedTemplate import TaggedTemplate

class TemplateHelper():
    def __init__(self):
        self.templates = {}
        self.static_params = []

    def add_template(self, template_filepath, tag = '__KP'):
        # Need KP_read_dir for COMPS

        print "Reading template from file:", template_filepath
        template_json = json2dict(template_filepath)

        template_filename = os.path.basename(template_filepath)
        template = TaggedTemplate(template_filename, template_json, tag)

        if template_filename in self.templates:
            warnings.warn("Already had template named " + template_filename + ".  Replacing previous template.")
        self.templates[template_filename] = template

    def set_static_params(self, static_params):
        self.static_params = static_params

    def set_dynamic_header_table(self, header, table):
        self.header = header
        self.table = table

        nParm = len(header)
        nRow = len(table)

        assert( nRow > 0 )
        for row in table:
            assert( nParm == len(row) )

        print "Table with %d configurations of %d parameters." % (nRow, nParm)

    def get_static_params(self):
        return self.static_params

    @staticmethod
    def path_to_address(path):
        address = ''
        for p in path:
            if isinstance(p, int):
                address = address + '.'+str(p)
            else:
                address = address + '.'+p
        return address[1:]

    def mod_dynamic_parameters(self, cb, dynamic_params):
        all_params = copy.deepcopy( self.static_params )
        all_params.update(dynamic_params)

        # Set campaign filename in config
        if 'CONFIG.Campaign_Filename' in all_params:
            campaign_filename = all_params['CONFIG.Campaign_Filename']
            print "Found campaign filename in header, setting Campaign_Filename to %s" % campaign_filename
            cb.config['parameters']['Campaign_Filename'] = campaign_filename
            del all_params['CONFIG.Campaign_Filename']

        # Set demographics filenames in config
        if 'CONFIG.Demographics_Filenames' in all_params:
            demographics_filenames = all_params['CONFIG.Demographics_Filenames']
            print "Found demographics filenames in header, setting Demographics_Filenames to %s" % demographics_filenames
            cb.config['parameters']['Demographics_Filenames'] = demographics_filenames
            del all_params['CONFIG.Demographics_Filenames']

        expanded_params = []

        # Modify static and dynamic parameters in _all_ template files
        # BETTER: Only do this for the selected files
        for template_filename, template in self.templates.iteritems():
            expanded_param_names = template.expand_tags(all_params.keys())

            for path_list, value in zip(expanded_param_names, all_params.values()):
                for path in path_list:
                    address = TemplateHelper.path_to_address(path)
                    expanded_params.append( (address,value) )

        # Set campaign file in cb
        campaign_filename = cb.config['parameters']['Campaign_Filename']
        if campaign_filename in self.templates:
            print "--> Found campaign template with filename %s, using template" % campaign_filename
            cb.campaign = self.templates[campaign_filename].contents

        # Set demographics files in cb
        demographics_filenames = copy.deepcopy(cb.config['parameters']['Demographics_Filenames'])
        for demographics_filename in demographics_filenames:
            if demographics_filename in self.templates:
                print "--> Found demographics template with filename %s, using template" % demographics_filename
                cb.add_input_file(demographics_filename.replace(".json",""), self.templates[demographics_filename].contents)


    def experiment_builder(self):
        # Note from_combos to include run_number
        return (
                ModBuilder.set_mods(
                    [
                        ModBuilder.ModFn(self.mod_dynamic_parameters, dict(zip(self.header, row)))
                    ]
                )
                for row in self.table
            )
