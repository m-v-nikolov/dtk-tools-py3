import json
import os
import validators
import types
import sys

default_schema_file = os.path.join(os.path.dirname(__file__),
                                   'config_schema.json')

boolean_values = [0, 1, "0", "1", True, False]


class IniValidator:

    def __init__(self, section_name, schema_file=''):

        self.section_name = section_name

        if not schema_file:
            schema_file = default_schema_file

        self.schema_file = schema_file

        if not os.path.exists(schema_file):
            raise Exception('IniValidator requires a schema file (' + schema_file + ').')

        f = open(schema_file, 'r')

        self.schema = json.loads(f.read())

        if self.section_name not in self.schema:
            print "Section: " + self.section_name + " not found in schema"
            sys.exit()

        self.schemaSection = self.schema["COMMON"]
        self.schemaSection += self.schema[self.section_name]

    def validate(self, setup_parser):

        # print "Validating ini file: " + setupParser.ini_file + ", section: " \
        #           + self.section_name + " with schema: " + self.schema_file

        for rule in self.schemaSection:

            val = setup_parser.get(rule["name"])

            if val is None:
                print "No section called: " + rule["name"]
            else:
                method = getattr(self, "validate_" + rule["type"])
                if not method(val, rule):
                    print "Validation failed for " + rule["name"] + "=" + val + " as type: " + rule["type"]
                    sys.exit()

    @staticmethod
    def validate_url(val, rule):
        return validators.url(val)

    @staticmethod
    def validate_string(val, rule):
        return isinstance(val, types.StringType)

    @staticmethod
    def validate_radio(val, rule):
        if "choices" not in rule:
            print "choices not found in rule: " + rule["name"]
            return False

        return val in rule["choices"]

    @staticmethod
    def validate_int(val, rule):
        return isinstance(int(val), types.IntType)

    @staticmethod
    def validate_bool(val, rule):
        return val in boolean_values

    @staticmethod
    def validate_directory(val, rule):
        if "optional" in rule and rule["optional"] is True and val is "":
            return True

        res = os.path.isdir(os.path.abspath(val))

        if res is not True:
            print "Directory validation failed: " + val

        return res

    @staticmethod
    def validate_file(val, rule):
        if "optional" in rule and rule["optional"] is True and val is "":
            return True

        res = os.path.isfile(os.path.abspath(val))

        if res is not True:
            print "File validation failed: " + val

        return res