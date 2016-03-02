import os
import sys
from ConfigParser import ConfigParser

default_setup = os.path.join(os.path.dirname(__file__),
                             'simtools.cfg')

def SetupParser(setup_file=''):
    '''
    Parse user settings and directory locations
    from setup configuration file: simtools.cfg
    '''

    if not setup_file:
        setup_file = default_setup

    if not os.path.exists(setup_file):
        raise Exception('SetupParser requires a setup file (' + setup_file + ') defining e.g. environmental variables.')

    setup = ConfigParser({'password':''})
    setup.read(setup_file)

    user = os.environ['USERNAME'] if sys.platform == 'win32' else os.getlogin()
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

    return setup
