import os
from simtools.SimConfigBuilder import SimConfigBuilder
from dtk.interventions.empty_campaign import empty_campaign
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.builders.ConfigurationJson import ConfigurationJson
from dtk.utils.builders.KPTaggedJson import KPTaggedJson

# TODO: Can the config file be selected dynamically?

class TemplateContainer(SimConfigBuilder):
    '''
    A container for json files of ConfigurationJson or KPTaggedJson class.
    '''

    config_template_key = 'CONFIG_TEMPLATE'    # handled differently from other template files

    def __init__(self, plugin_files_json, plugin_files_dir):

        self.plugin_files_json = json2dict(plugin_files_json)
        self.plugin_files_dir = plugin_files_dir

        self.templates = {}

        # TODO: Ensure unique filenames
        self.load_templates()

    def __iter__(self):
        return iter(self.templates)

    def next(self):
        return self.templates.next()

    def load_templates(self):
        for template_type in self.plugin_files_json.keys():
            is_config = template_type == self.config_template_key
            for plugin_filename in self.plugin_files_json[template_type]:
                fn = os.path.join( self.plugin_files_dir, plugin_filename)
                print('Loading %s as %s' % (fn, template_type))
                contents = json2dict(fn)

                if is_config:
                    new_template = ConfigurationJson(contents, plugin_filename)
                else:
                    new_template = KPTaggedJson(contents, plugin_filename)

                self.templates[plugin_filename] = new_template

    def get(self, filename):
        if filename not in self.templates:
            return None

        return self.templates[filename]

    def get_by_type(self, template_type):
        ret = []
        if template_type not in self.plugin_files_json.keys():
            print 'ERROR, no templates of type %s were listed in plugin files' % template_type

        for fn in self.plugin_files_json[template_type]:
            ret.append(self.get(fn))

        return ret

    def update_params(self, params):
        # SHOULD MAP FIRST!
        for param_name,val in params.items():
            param_split = param_name.split('.')
            param_type = param_split[0]
            param_name = '.'.join(param_split[1:])
            print param_type
            print param_name
            template_type = param_type + '_TEMPLATE'
            for fn in  self.plugin_files_json[template_type]:
                print '[%s]: setting params:'%fn,params
                self.get(fn).update_params(params)
