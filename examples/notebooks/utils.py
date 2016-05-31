import os
import site
import ConfigParser
import imp
import time

import pandas as pd
from IPython.display import display

from dtk.utils.core.DTKSetupParser import DTKSetupParser
from simtools.ExperimentManager import ExperimentManagerFactory

def write_dtk_config(max_sims, sim_root, input_root, bin_path, exe_path):
    currentDir = os.path.dirname(os.path.abspath(__file__))
    conf_path = os.path.join(currentDir, '..', '..', 'simtools', 'simtools.cfg')
    print conf_path
    config = ConfigParser.RawConfigParser()
    config.read(conf_path)

    config.set('LOCAL', 'max_local_sims', max_sims)
    config.set('LOCAL', 'sim_root', sim_root)
    config.set('LOCAL', 'input_root', input_root)
    config.set('LOCAL', 'bin_root', bin_path)
    config.set('BINARIES', 'exe_path', exe_path)

    with open(conf_path, 'wb') as configfile:
        config.write(configfile)
    
    #make sure the simulations dir exists
    if not os.path.exists(sim_root):
        os.mkdir(sim_root)

    print "The simtools.cfg file has been successfully updated!"


def test_if_dtk_present():
    try:
        imp.find_module('dtk')
        print "The DTK module is present and working!"
    except ImportError:
        print "The DTK module is not present... Make sure it is properly installed and imported!"


def test_if_simulation_done(states):
    if states.values()[0] == "Finished":
        print "The simulation completed successfully!"
    else:
        print "A problem has been encountered. Please try to run the code block again."


def get_sim_manager():
    exe_path = DTKSetupParser().get('BINARIES','exe_path')
    return ExperimentManagerFactory.from_model(exe_path, 'LOCAL')


def run_demo(sm, run_sim_args, verbose=True):
    sm.run_simulations(**run_sim_args)
    if verbose:
        display(sm.exp_data)


def monitor_status(sm, verbose=True):
    while True:
        states, msgs = sm.get_simulation_status()
        if sm.status_finished(states): 
            break
        else:
            if verbose:
                sm.print_status(states, msgs)
            time.sleep(3)
    sm.print_status(states, msgs)


def draw_plots(sm, analyzers):
    sm.analyzers = analyzers
    sm.analyze_simulations()