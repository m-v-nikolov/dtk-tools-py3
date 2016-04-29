import os
import sys
from ConfigParser import ConfigParser

from simtools.SetupParser import SetupParser

def DTKSetupParser(setup_file=''):
    '''
    Parse user settings and directory locations
    from setup configuration file: dtk_setup.cfg

    And overlay on top of settings from simtools.SetupParser
    '''

    if not setup_file:
        setup_file = os.path.join(os.path.dirname(__file__), '..', '..', 'dtk_setup.cfg')

    if not os.path.exists(setup_file):
        raise Exception('DTKSetupParser requires a setup file (' + setup_file + ') defining e.g. environmental variables.')

    dtk_setup = ConfigParser({'password':''})
    dtk_setup.read(setup_file)

    if sys.platform == 'win32':
        user = os.environ['USERNAME']
    else:
        import pwd
        user = pwd.getpwuid(os.geteuid())[0]

    setup = SetupParser()
    for section in dtk_setup.sections():
        dtk_setup.set(section, 'user', user)
        if not setup.has_section(section):
            setup.add_section(section)
        for param, value in dtk_setup.items(section):
            setup.set(section, param, value)

    return setup
