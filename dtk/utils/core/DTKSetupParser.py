import os
import sys
from ConfigParser import ConfigParser  # to parse dtk_setup.cfg

def DTKSetupParser(setup_file=''):

    if not setup_file:
        setup_file = os.path.join( os.path.dirname(__file__), '../../dtk_setup.cfg' )

    if not os.path.exists(setup_file):
        raise Exception('DTKSetupParser requires a setup file (' + setup_file + ') defining e.g. environmental variables.')

    user=os.environ['USERNAME'] if sys.platform == 'win32' else os.getlogin()

    setup = ConfigParser({'password':''})
    setup.read(setup_file)
    setup.set('HPC', 'user', user)
    setup.set('BINARIES', 'user', user)

    # Add a fallback in case max_threads is not set
    if not setup.has_option('LOCAL','max_threads'):
        if (setup.has_option('HPC','max_threads')):
            setup.set('LOCAL','max_threads',setup.get('HPC','max_threads'))
            print "/!\\ Please update your dtk_config.cfg and change max_threads from HPC to LOCAL /!\\"
        else:
            print "/!\\ Please update your dtk_config.cfg and set max_threads in LOCAL. Fallback value (16) used /!\\"
            setup.set('LOCAL','max_threads','16')

    return setup
