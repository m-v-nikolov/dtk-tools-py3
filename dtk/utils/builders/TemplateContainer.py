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

                if template_type not in self.templates:
                    self.templates[template_type] = [new_template]
                else:
                    self.templates[template_type].append( new_template )

    def get_by_name(self, filename, template_type):
        if template_type not in self.templates:
            return None

        for template in self.templates[template_type]:
            if template.filename == filename:
                return template

        return None


    def get_by_type(self, template_type):
        if template_type not in self.templates:
            return None

        return self.templates[template_type]
