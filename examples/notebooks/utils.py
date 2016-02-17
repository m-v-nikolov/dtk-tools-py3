import os
import site
import ConfigParser
import imp
import time

import pandas as pd
from IPython.display import display

from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.simulation.SimulationManager import SimulationManagerFactory


def write_dtk_config(max_sims, sim_root, input_root, bin_path, exe_path, current_path):
    conf_path = os.path.join(current_path, 'dtk_setup.cfg')
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

    print "The dtk_config.cfg file has been successfully updated!"


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
    dtk_setup_path = os.path.join(os.path.dirname(os.path.abspath('__file__')),"dtk_setup.cfg")
    exe_path = DTKSetupParser().get('BINARIES','exe_path')
    return SimulationManagerFactory.from_exe(exe_path, 'LOCAL',setup_file=dtk_setup_path)


def run_demo(sm, run_sim_args, verbose=True):
    sm.RunSimulations(**run_sim_args)
    if verbose:
        display(sm.exp_data)


def monitor_status(sm, verbose=True):
    while True:
        states, msgs = sm.SimulationStatus()
        if sm.statusFinished(states): 
            break
        else:
            if verbose:
                sm.printStatus(states, msgs)
            time.sleep(3)
    sm.printStatus(states, msgs)


def draw_plots(sm, analyzers):
    sm.analyzers = analyzers
    sm.AnalyzeSimulations()