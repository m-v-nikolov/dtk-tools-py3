import json
import os
import sys
from ConfigParser import ConfigParser

default_setup = os.path.join(os.path.dirname(__file__),
                             'simtools.cfg')

class SetupParser():
    '''
    Parse user settings and directory locations
    from setup configuration file: simtools.cfg
    '''

    def __init__(self, setup_file=''):
        self.schema = None
        self.setup = None

        if not setup_file:
            setup_file = default_setup

        if not os.path.exists(setup_file):
            raise Exception('SetupParser requires a setup file (' + setup_file + ') defining e.g. environmental variables.')

        setup = ConfigParser({'password':''})
        setup.read(setup_file)

        if sys.platform == 'win32':
            user = os.environ['USERNAME']
        else:
            import pwd
            user = pwd.getpwuid(os.geteuid())[0]

# Diff copied from DTKSetupParser. Needs validation to see if it is still applicable.
        for section in setup.sections():
            setup.set(section, 'user', user)
            if not setup.has_section(section):
                setup.add_section(section)
            for param, value in setup.items(section):
                setup.set(section, param, value)
# End diff

        setup.set('HPC', 'user', user)
        setup.set('LOCAL', 'user', user)

        # Overwrite local paths with Mac/Linux versions
        if os.name == 'posix':
            setup.set('POSIX', 'user', user)
            for param, value in setup.items('POSIX'):
                setup.set('LOCAL', param, value)

        # Add a fallback in case max_threads is not set
        if not setup.has_option('GLOBAL', 'max_threads'):
            print("/!\\ Please update your simtools.cfg and set max_threads in GLOBAL. Fallback value (16) used /!\\")
            if not setup.has_section('GLOBAL'):
                setup.add_section('GLOBAL')
            setup.set('GLOBAL', 'max_threads', '16')

        self.setup = setup

    def get(self, category, parameter):
        return self.setup.get(category, parameter)

    def has_section(self, section):
        return self.setup.has_section(section)

    def set(self, category, parameter, value):
        self.setup.set(category, parameter, value)

    def items(self, category):
        return self.setup.items(category)

    def getboolean(self,category, param):
        return self.setup.getboolean(category, param)

    def load_schema(self):
        json_schema = json.load(open(os.path.join(os.path.dirname(os.path.realpath(__file__)), "config_schema.json")))
        self.schema = json_schema
        return json_schema
