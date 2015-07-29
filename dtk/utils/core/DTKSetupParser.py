import os
import sys
from ConfigParser import ConfigParser  # to parse dtk_setup.cfg

def DTKSetupParser(setup_file=''):

    if not setup_file:
        setup_file = os.path.join( os.path.dirname(__file__), '../../../dtk_setup.cfg' )

    if not os.path.exists(setup_file):
        raise Exception('DTKSetupParser requires a setup file (' + setup_file + ') defining e.g. environmental variables.')

    user=os.environ['USERNAME'] if sys.platform == 'win32' else os.getlogin()

    setup = ConfigParser({'password':''})
    setup.read(setup_file)
    setup.set('HPC', 'user', user)
    setup.set('BINARIES', 'user', user)

    return setup
