import copy
import os
import logging

from simtools.ModBuilder import ModBuilder
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.builders.TaggedTemplate import TaggedTemplate

logger = logging.getLogger(__name__)

class TemplateHelper():

    static_params = []

    def __init__(self, _static_params):
        self.templates = {}
        self.static_params = _static_params

    def add_template(self, template_filepath, tag = '__KP'):
        """
        Add a template to the template helper.

        :param template_filepath: The path to the file on disk.
        :param tag: The tag prefix that has been added at desired locations in the template file.  Tags are added adjacent to the desired location, and have a matching prefix.  Tags must begin with two underscores.  For example, consider this Example.json:

        Example.json:
        {
            "Example":
            [
                {
                    "Parameter": 1
                },
                {
                    "Parameter__KP_Set_This_Parameter": "<-- MARKER (This value does not matter, but is needed to maintain valid JSON format)",
                    "Parameter": 2
                },
                {
                    "Parameter__KP_Set_This_Parameter": "<-- MARKER (This value does not matter, but is needed to maintain valid JSON format)",
                    "Parameter": 3
                }
            ]
        }

        To set the second and third instances "Parameter" in the array, use tagged parameter Parameter__KP_Set_This_Parameter.  This tagged parameter will be expanded to two separate addresses:
        1. Example[1]['Parameter']
        2. Example[2]['Parameter']
        The value you provide will be set at all matching addresses.
        """

        assert( tag[:2] == '__' )

        # Read in template
        logger.info( "Reading template from file:", template_filepath )
        template_json = json2dict(template_filepath)

        # Get the filename and create a TaggedTemplate
        template_filename = os.path.basename(template_filepath)
        template = TaggedTemplate(template_filename, template_json, tag)

        if template_filename in self.templates:
            logger.warning("Already had template named " + template_filename + ".  Replacing previous template.")

        # Set static tag parameters
        for param,value in self.static_params.iteritems():
            if tag in param:
                tags = template.set_param(param, value)

        # Store the template in a dictionary
        self.templates[template_filename] = template

    def set_dynamic_header_table(self, header, table):
        """
        Set the header and table for dynamic (per-simulation) configuration.

        :param header: Containes the parameter addresses, using the special tags (e.g. __KP).  Here is an example:
            header = [  'Campaign_Filename', 'Start_Year__KP_Seeding_Year', 'Society__KP_Bulawayo.INFORMAL.Relationship_Parameters.Coital_Act_Rate' ]

        :param table: Containes the parameter values.  One simulation will be created for each row, e.g.:
            table = [
                [ 'campaign_outbreak_only.json', 1990, 2],
                [ 'campaign.json', 1980, 1 ]
            ]
        """

        self.header = header
        self.table = table

        nParm = len(header)
        nRow = len(table)

        assert( nRow > 0 )
        for row in table:
            assert( nParm == len(row) )

        logger.info( "Table with %d configurations of %d parameters." % (nRow, nParm) )

    def __mod_dynamic_parameters(self, cb, dynamic_params):
        logger.info( '-----------------------------------------' )
        #all_params = copy.deepcopy( self.static_params )
        #all_params.update(dynamic_params)
        all_params = copy.deepcopy(dynamic_params)
        active_template_files = []

        # Set campaign filename in config
        if 'Campaign_Filename' in all_params:
            campaign_filename = all_params['Campaign_Filename']
            logger.info( "Found campaign filename in header, setting Campaign_Filename to %s" % campaign_filename )
            cb.set_param('Campaign_Filename', campaign_filename)
            del all_params['Campaign_Filename']

        campaign_filename = cb.config['parameters']['Campaign_Filename']
        if campaign_filename in self.templates:
            logger.info( "--> Found campaign template with filename %s, using template" % campaign_filename )
            active_template_files.append(campaign_filename)

        # Set demographics filenames in config
        if 'Demographics_Filenames' in all_params:
            demographics_filenames = all_params['Demographics_Filenames']
            logger.info( "Found demographics filenames in header, setting Demographics_Filenames to %s" % demographics_filenames )
            cb.set_param('Demographics_Filenames', demographics_filenames)
            del all_params['Demographics_Filenames']

        demographics_filenames = copy.deepcopy(cb.config['parameters']['Demographics_Filenames'])
        for demographics_filename in demographics_filenames:
            if demographics_filename in self.templates:
                logger.info( "--> Found demographics template with filename %s, using template" % demographics_filename )
                active_template_files.append(demographics_filename)

        # CONFIG parameters - not too happy about this.  The only I can tell they're confi parameters
        # is if the parameter name DOES NOT contain two underscores, which started the tag, e.g. __KP.
        # Any thoughts of how to do this better?  E.g. what if config parameter has __ in it?
        config_params = {p:v for p,v in self.static_params.iteritems() if '__' not in p}
        config_params.update( {p:v for p,v in all_params.iteritems() if '__' not in p} )
        for param, value in config_params.iteritems():
            logger.info( "Setting " + param + " = " + str(value) )
            cb.set_param(param,value)
            if param in all_params:
                del all_params[param]

        templates_mod = { template_filename : copy.deepcopy(self.templates[template_filename]) 
            for template_filename in active_template_files }

        # Modify static and dynamic parameters in active templates
        for template_filename in active_template_files:
            template = templates_mod[template_filename]
            for key, value in all_params.iteritems():
                template.set_param(key,value)

        # Set campaign file in cb
        if campaign_filename in self.templates:
            cb.campaign = templates_mod[campaign_filename].contents

        # Set demographics files in cb
        for demographics_filename in demographics_filenames:
            if demographics_filename in self.templates:
                cb.add_input_file(demographics_filename.replace(".json",""), templates_mod[demographics_filename].contents)


    def experiment_builder(self):
        """
        Returns a ModBuilder ModFn that sets file contents and values in config builder according to the dynamic parameters.
        """
        return [
            ModBuilder.ModFn(self.__mod_dynamic_parameters, dict(zip(self.header, row)))
            for row in self.table
        ]
