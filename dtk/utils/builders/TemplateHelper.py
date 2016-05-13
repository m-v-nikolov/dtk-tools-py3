from simtools.ModBuilder import ModBuilder
from dtk.utils.parsers.JSON import json2dict
from dtk.utils.builders.KPTaggedJson import KPTaggedJson

class TemplateHelper():
    def __init__(self):
        self.templates = {}

    def add_template(self, template_filename, static_params):
        # Also need KP_read_dir

        print "Reading template from file:", template_filename
        template = KPTaggedJson(template_filename)

        print "Overriding static params:", static_params
        template.update_params(static_params)
        self.templates[template_filename] = template

    def set_dynamic_header_table(self, header, table):
        self.header = header
        self.table = table

        nParm = len(header)
        nRow = len(table)

        assert( nRow > 0 )
        for row in table:
            assert( nParm == len(row) )

        print "Table with %d configurations of %d parameters." % (nRow, nParm)

    def mod_dynamic_parameters(cb, header, row):
        print "mod_dynamic_parameters with:"
        print "--> cb", cb
        print "--> header", header
        print "--> row", row

    def experiment_builder(self):
        # Note from_combos to include run_number
        return ModBuilder.set_mods(
            [
                ModBuilder.ModFn(self.mod_dynamic_parameters, zip(self.header, row))
                for row in self.table
            ]
        )
