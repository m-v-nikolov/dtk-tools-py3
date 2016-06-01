import copy
import logging

from simtools.ModBuilder import ModBuilder

logger = logging.getLogger(__name__)

class TemplateHelper():
    # A helper class for templates.

    def set_dynamic_header_table(self, header, table):
        """
        Set the header and table for dynamic (per-simulation) configuration.
        The header has two special keywords: 
        * ACTIVE_TEMPLATES:
        * TAGS:

        :param header: Containes the parameter addresses, using the special tags (e.g. __KP).  Here is an example:
            header = [  'ACTIVE_TEMPLATES', 'Start_Year__KP_Seeding_Year', 'Society__KP_Bulawayo.INFORMAL.Relationship_Parameters.Coital_Act_Rate', 'TAGS' ]

        :param table: Containes the parameter values.  One simulation will be created for each row, e.g.:
            table = [
                [ [config1, campaign],               1980, 1, ['Tag1']         ],
                [ [config2, campaign_outbreak_only], 1990, 2, ['Tag2', 'Tag3'] ]
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
        # Modify the config builder according to the dynamic_parameters

        logger.info( '-----------------------------------------' )
        all_params = copy.deepcopy(dynamic_params)

        if 'ACTIVE_TEMPLATES' in all_params:
            active_templates = all_params.pop('ACTIVE_TEMPLATES')
            for template in active_templates:
                logger.debug( "Active templates: %s" % [t.get_filename() for t in active_templates] )

        # For error checking, union all tags and active template filenames
        # TODO: Better.  map or function asking each active template if it has a key?
        '''
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
        '''

        tags = []
        for template in active_templates:
            new_tags = template.set_params_and_modify_cb(all_params, cb)
            tags.append(new_tags)


    def get_modifier_functions(self):
        """
        Returns a ModBuilder ModFn that sets file contents and values in config builder according to the dynamic parameters.
        """
        return [
            ModBuilder.ModFn(self.__mod_dynamic_parameters, dict(zip(self.header, row)))
            for row in self.table
        ]
