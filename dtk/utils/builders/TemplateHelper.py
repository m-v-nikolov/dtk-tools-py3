import copy
import logging

from simtools.ModBuilder import ModBuilder, ModFn

#logger = logging.getLogger(__name__)


class TemplateHelper():
    # A helper class for templates.

    active_templates = []

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
                [ [config1, campaign],               1980, 0.1, {'Tag1':'Value1'}              ],
                [ [config2, campaign_outbreak_only], 1990, 0.2, {'Tag2':None, 'Tag3':'Value3'} ]
            ]
        """

        self.header = header
        self.table = table

        nParm = len(header)
        nRow = len(table)

        assert (nRow > 0)
        for row in table:
            assert (nParm == len(row))

        #logger.info("Table with %d configurations of %d parameters." % (nRow, nParm))

    def mod_dynamic_parameters(self, cb, dynamic_params):
        # Modify the config builder according to the dynamic_parameters

        #logger.info('-----------------------------------------')
        all_params = copy.deepcopy(dynamic_params)

        tags = {}
        if 'TAGS' in all_params:
            taglist = all_params.pop('TAGS')
            tags.update(taglist)

        if 'ACTIVE_TEMPLATES' in all_params:
            self.active_templates = all_params.pop('ACTIVE_TEMPLATES')
            #for template in self.active_templates:
            #    logger.debug("Active templates: %s" % [t.get_filename() for t in self.active_templates])

        if not self.active_templates:
            raise Exception("No templates are active!")

        # Error checking.  Make sure all dynamic parameters will be found in at least one place.
        for param in all_params:
            found = False
            for template in self.active_templates:
                if not found and template.has_param(param):
                    found = True
            if not found:
                active_template_filenames = [t.get_filename() for t in self.active_templates]
                raise Exception("None of the active templates consume parameter %s.  Active templates: %s." % (
                param, active_template_filenames))

        for template in self.active_templates:
            new_tags = template.set_params_and_modify_cb(all_params, cb)
            if new_tags:
                tags.update(new_tags)

        return tags

    def get_modifier_functions(self):
        """
        Returns a ModBuilder ModFn that sets file contents and values in config builder according to the dynamic parameters.
        """
        return [
            ModFn(self.mod_dynamic_parameters, dict(zip(self.header, row)))
            for row in self.table
            ]
