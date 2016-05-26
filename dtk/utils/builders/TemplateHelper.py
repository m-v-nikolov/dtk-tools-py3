import copy
import logging

from simtools.ModBuilder import ModBuilder

logger = logging.getLogger(__name__)

class TemplateHelper():
    # A helper class for templates.

    def __init__(self):
        self.config_template = None
        self.campaign_template = None
        self.demographic_templates = None

    def set_dynamic_header_table(self, header, table):
        """
        Set the header and table for dynamic (per-simulation) configuration.
        The header has three special values: CONFIG_TEMPLATE, CAMPAIGN_TEMPLATE, and DEMOGRAPHICS_TEMPLATES.  These keywords allow the config, campaign, and demographics files to be set and likely modified using tags on a per-simulation basis.  Values in the table corresponding to these header keywords are TaggedTemplate instanes for CONFIG_TEMPLATE and CAMPAIGN_TEMPLATE, and a list of TaggedTempalte for DEMOGRAPHICS_TEMPLATES.  The CONFIG_TEMPLATE and CAMPAIGN_TEMPLATE will be set to the corresponding config and campaign files in the config builder.  DEMOGRAPHICS_TEMPLATES will get added as additional simulation input files, and thus appear in the simulation working directory.  There is a check to make sure that, at the end of configuration, each demographic template file name has an entry in config builder's Demographics_Filenames parameter.

        :param header: Containes the parameter addresses, using the special tags (e.g. __KP).  Here is an example:
            header = [  'CAMPAIGN_TEMPLATE', 'Start_Year__KP_Seeding_Year', 'Society__KP_Bulawayo.INFORMAL.Relationship_Parameters.Coital_Act_Rate' ]

        :param table: Containes the parameter values.  One simulation will be created for each row, e.g.:
            table = [
                [ campaign, 1980, 1 ],
                [ campaign_outbreak_only, 1990, 2]
            ]
        In this example, campaign and campaign_outbreak_only are instances of TaggedTemplate.
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
        # Modify the config builder according to the dynamic_parameters

        logger.info( '-----------------------------------------' )
        all_params = copy.deepcopy(dynamic_params)

        # Handle dynamic config template
        if 'CONFIG_TEMPLATE' in all_params:
            conifg_template = all_params.pop('CONFIG_TEMPLATE')
            self.config_template = config_template
            logger.info( "Using config template: %s" % config_template.filename )

        # Handle dynamic campaign template
        if 'CAMPAIGN_TEMPLATE' in all_params:
            campaign_template = all_params.pop('CAMPAIGN_TEMPLATE')
            self.campaign_template = campaign_template
            logger.info( "Using campaign template: %s" % campaign_template.filename )

        # Handle dynamic demographics templates
        if 'DEMOGRAPHICS_TEMPLATES' in all_params:
            demographics_templates = all_params.pop('DEMOGRAPHICS_TEMPLATES')
            self.demographic_templates = demographics_templates
            logger.info( "Using demographics templates: %s" % [d.filename for d in demographics_templates] )

        # For error checking, union all tags and active template filenames
        # TODO: Better.  map or function asking each active template if it has a key?
        tag_list = set()
        active_template_filenames = []
        if self.config_template is not None:
            [tag_list.add(k) for k in self.config_template.tag_dict.keys() ]
            active_template_filenames.append( self.config_template.filename )
        if self.campaign_template is not None:
            [tag_list.add(k) for k in self.campaign_template.tag_dict.keys() ]
            active_template_filenames.append( self.campaign_template.filename )
        if self.demographic_templates is not None:
            for d in self.demographic_templates:
                [tag_list.add(k) for k in d.tag_dict.keys() ]
                active_template_filenames.append( d.filename )

        # Error checking.  Make sure all dynamic parameters will be found in at least one place.
        for param in all_params.keys():
            tag = param.split('.')[0]
            if tag not in tag_list:
                raise Exception("Could not find tag in any active template.\n--> Tag: %s\n--> Available tags: %s.\n--> Active templates: %s." % (tag, tag_list, active_template_filenames) )

        # Modify static and dynamic parameters in templates
        # --> CONFIG
        if self.config_template is not None:
            config_template_mod = copy.deepcopy( self.config_template ) # Deep copy needed?
            config_template_mod.set_params(all_params)
            cb.config = self.config_template.contents

        # --> CAMPAIGN
        if self.campaign_template is not None:
            campaign_template_mod = copy.deepcopy( self.campaign_template ) # Deep copy needed?
            campaign_template_mod.set_params(all_params)

            cb.set_param('Campaign_Filename', campaign_template_mod.filename)
            cb.campaign = campaign_template_mod.contents

        # --> DEMOGRAPHICS
        if self.demographic_templates is not None:
            demographics_filenames = cb.params['Demographics_Filenames']
            for d in self.demographic_templates:
                # Make sure the filename is listed in Demographics_Filenames
                if d.filename not in demographics_filenames:
                    raise Exception( "Using template with filename %s for demographics, but this filename is not included in Demographics_Filenames: %s", d.filename, demographics_filenames)

                demog_template_mod = copy.deepcopy( d ) # Deep copy needed?
                demog_template_mod.set_params(all_params)

                cb.add_input_file(demog_template_mod.filename.replace(".json",""), demog_template_mod.contents)

    def get_modifier_functions(self):
        """
        Returns a ModBuilder ModFn that sets file contents and values in config builder according to the dynamic parameters.
        """
        return [
            ModBuilder.ModFn(self.__mod_dynamic_parameters, dict(zip(self.header, row)))
            for row in self.table
        ]
