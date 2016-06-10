import json
import os
import sys
from ConfigParser import ConfigParser


class SetupParser:
    """
    Parse user settings and directory locations
    from setup configuration file: simtools.cfg
    """
    selected_block = None

    def __init__(self, selected_block='LOCAL', setup_file=''):
        # Store the selected_block in the class
        if not SetupParser.selected_block:
            SetupParser.selected_block = selected_block

        # First, always load the defaults
        self.setup = ConfigParser()
        self.setup.read(os.path.join(os.path.dirname(__file__), 'simtools.ini'))

        # Then overlays the eventual setup_file passed or simtools.ini in working dir
        overlay_path = None
        if setup_file and os.path.exists(setup_file):
            overlay_path = setup_file
        elif os.path.exists(os.path.join(os.getcwd(), 'simtools.ini')):
            overlay_path = os.path.join(os.getcwd(), 'simtools.ini')

        # Add the user to the default
        if sys.platform == 'win32':
            user = os.environ['USERNAME']
        else:
            import pwd
            user = pwd.getpwuid(os.geteuid())[0]
        self.setup.set('DEFAULT', 'user', user)

        # If we found an overlay applies it
        if overlay_path:
            overlay = ConfigParser()
            overlay.read(overlay_path)
            # Add the user just in case
            overlay.set('DEFAULT','user',user)

            # Overlay
            self.overlay_setup(overlay)

        # If the selected block is type=HPC, take care of HPC initialization
        if self.get('type') == "HPC":
            try:
                os.environ['COMPS_REST_HOST'] = self.get('server_endpoint')
                from pyCOMPS import pyCOMPS

            except ImportError:
                print('Failed loading pyCOMPS package; you will only be able to run local simulations.')

            except KeyError:
                print('Unable to determine JAVA_HOME; please set JAVA_HOME environment variable as described in pyCOMPS README.txt')

        # Validate
        self.validate()


    def overlay_setup(self,cp):
        # If the cp doesnt have the selected block, no need of overlaying
        if not cp.has_section(self.selected_block):
            return

        # If the current section doesnt exist in the current setup ->create it
        if not self.setup.has_section(self.selected_block):
            # Create the section
            self.setup.add_section(self.selected_block)

            # Depending on the type grab the default from HPC or LOCAL
            for item in self.setup.items(cp.get(self.selected_block,'type')):
                self.setup.set(self.selected_block, item[0], item[1])

        # Go through all the parameters of the cp for the selected_block and overlay them to the current section
        for item in cp.items(self.selected_block):
            self.setup.set(self.selected_block,item[0], item[1])

    def get(self, parameter):
        if not self.setup.has_option(self.selected_block, parameter):
            raise ValueError("%s block does not have the option %s!" % (self.selected_block, parameter))
        return self.setup.get(self.selected_block,parameter)

    def set(self, parameter, value):
        self.setup.set(self.selected_block, parameter, value)

    def items(self):
        return self.setup.items(self.selected_block)

    def getboolean(self, param):
        return self.setup.getboolean(self.selected_block, param)

    def load_schema(self):
        json_schema = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_schema.json")))
        self.schema = json_schema
        return json_schema

    def file_name(self):
        return self.ini_file

    def validate(self):
        pass
