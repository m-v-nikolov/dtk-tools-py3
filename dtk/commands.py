import argparse
from importlib import import_module
import json
import logging
import os
import sys
import time

import simtools.utils as utils

from dtk.utils.analyzers import StdoutAnalyzer
from simtools.ExperimentManager import ExperimentManagerFactory

from simtools.SetupParser import SetupParser

def load_config_module(config_name):
    sys.path.append(os.getcwd())
    module_name = os.path.splitext(os.path.basename(config_name))[0]
    return import_module(module_name)


def run(args):
    # get simulation-running instructions from script
    mod = load_config_module(args.config_name)

    # run the simulation
    location = 'HPC' if (args and args.hpc) else 'LOCAL'
    setup = SetupParser()
    additional_args = {}
    if location == 'HPC':
        if args.priority:
            additional_args['priority'] = args.priority
        if args.node_group:
            additional_args['node_group'] = args.node_group
    sm = ExperimentManagerFactory.from_setup(setup, location, **additional_args)
    sm.run_simulations(**mod.run_sim_args)


def status(args):
    if args.active:
        logging.info('Getting status of all active experiments.')
        sms = reload_active_experiments()
        for sm in sms:
            states, msgs = sm.get_simulation_status()
            sm.print_status(states, msgs)
        return

    sm = reload_experiment(args)
    while True:
        states, msgs = sm.get_simulation_status()
        sm.print_status(states, msgs)
        if not args.repeat or sm.finished():
            break
        else:
            time.sleep(20)

def resubmit(args):
    sm = reload_experiment(args)

    if args.simIds:
        logging.info('Resubmitting job(s) with ids: ' + str(args.simIds))
        params = { 'ids': args.simIds }
    else:
        logging.info('No job IDs were specified.  Resubmitting all failed and canceled jobs in experiment.')
        params = { 'resubmit_all_failed': True }

    if args.all:
        sms = reload_experiments(args)
        for sm in sms:
            sm.resubmit_simulations(**params)
    else:
        sm = reload_experiment(args)
        sm.resubmit_simulations(**params)

def kill(args):

    if args.simIds:
        logging.info('KIlling job(s) with ids: ' + str(args.simIds))
        params = { 'ids': args.simIds }
    else:
        logging.info('No job IDs were specified.  Killing all jobs in selected experiment (or most recent).')
        params = { 'killall': True }

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logging.info('No action taken.')
        return

    if args.all:
        sms = reload_experiments(args)
        for sm in sms:
            sm.cancel_simulations(**params)
    else:
        sm = reload_experiment(args)
        sm.cancel_simulations(**params)

def stdout(args):
    logging.info('Getting stdout..')

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()

    if not args.force:
        if not sm.status_succeeded(states):
            logging.warning('Not all jobs have finished successfully yet...')
            logging.info('Job states:')
            logging.info(json.dumps(states, sort_keys=True, indent=4))
            return

    sm.add_analyzer(StdoutAnalyzer(args.simIds))

    if args.comps:
        utils.override_HPC_settings(sm.setup, use_comps_asset_svc='1')

    sm.analyze_simulations()

def analyze(args):

    logging.info('Analyzing results...')

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()

    if not args.force:
        if not sm.status_succeeded(states):
            logging.warning('Not all jobs have finished successfully yet...')
            logging.info('Job states:')
            logging.info(json.dumps(states, sort_keys=True, indent=4))
            return
        
    analyze_from_script(args, sm)

    if args.comps:
        utils.override_HPC_settings(sm.setup, use_comps_asset_svc='1')

    sm.analyze_simulations()

    import matplotlib.pyplot as plt  # avoid OS X conflict with Tkinter COMPS authentication
    plt.show()


def analyze_from_script(args, sim_manager):
    # get simulation-analysis instructions from script
    mod = load_config_module(args.config_name)

    # analyze the simulations
    for analyzer in mod.analyzers:
        sim_manager.add_analyzer(analyzer)


def reload_experiment(args=None):
    if args:
        id = args.expId
    else:
        id = None

    return ExperimentManagerFactory.from_file(utils.exp_file(id))

def reload_experiments(args=None):
    if args:
        id = args.expId
    else:
        id = None

    return [ExperimentManagerFactory.from_file(file, suppressLogging = True) for file in utils.exp_files(id)]

def reload_active_experiments(args=None):
    return [sm for sm in reload_experiments(args) if not sm.finished()]


def main():

    parser = argparse.ArgumentParser(prog='dtk')
    subparsers = parser.add_subparsers()

    # 'dtk run' options
    parser_run = subparsers.add_parser('run', help = 'Run one or more simulations configured by run-options.')
    parser_run.add_argument(dest = 'config_name', default = None, help = 'Name of configuration python script for custom running of simulation.')
    parser_run.add_argument('--hpc', action = 'store_true', help = 'Run simulation on HPC using COMPS (default is local simulation).')
    parser_run.add_argument('--priority', default = None, help = 'Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default = None, help = 'Specify node group of COMPS simulation (only for HPC).')
    parser_run.set_defaults(func = run)

    # 'dtk status' options
    parser_status = subparsers.add_parser('status', help = 'Report status of simulations in experiment specified by ID or name.')
    parser_status.add_argument(dest = 'expId', default = None, nargs = '?', help = 'Experiment ID or name.')
    parser_status.add_argument('-r', '--repeat', action = 'store_true', help = 'Repeat status check until job is done processing.')
    parser_status.add_argument('-a', '--active', action = 'store_true', help = 'Get the status of all active experiments (mutually exclusive to all other options).')
    parser_status.set_defaults(func = status)

    # 'dtk resubmit' options
    parser_resubmit = subparsers.add_parser('resubmit', help = 'Resubmit failed or canceled simulations specified by experiment ID or name.')
    parser_resubmit.add_argument(dest = 'expId', default = None, nargs = '?', help = 'Experiment ID or name.')
    parser_resubmit.add_argument('-s', '--simIds', dest = 'simIds', default = None, nargs = '+', help = 'Process or job IDs of simulations to resubmit.')
    parser_resubmit.add_argument('-a', '--all', action = 'store_true', help = 'Resubmit all failed or canceled simulations in selected experiments.')
    parser_resubmit.set_defaults(func = resubmit)

    # 'dtk kill' options
    parser_kill = subparsers.add_parser('kill', help = 'Kill running experiment specified by ID or name.')
    parser_kill.add_argument(dest = 'expId', default = None, nargs = '?', help =' Experiment ID or name.')
    parser_kill.add_argument('-s', '--simIds', dest = 'simIds', default = None, nargs = '+', help = 'Process or job IDs of simulations to kill.')
    parser_kill.add_argument('-a', '--all', action = 'store_true', help = 'Kill all simulations in (possibly multiple) selected experiments.')
    parser_kill.set_defaults(func = kill)

    # 'dtk stdout' options
    parser_stdout = subparsers.add_parser('stdout', help = 'Print stdout from simulation.')
    parser_stdout.add_argument(dest = 'expId', default = None, nargs = '?', help =' Experiment ID or name.')
    parser_stdout.add_argument('-s', '--simIds', dest = 'simIds', default = None, nargs = '+', help = 'Process or job IDs of simulations to print.')
    parser_stdout.add_argument('-c', '--comps', action='store_true', help = 'Use COMPS asset service to read output files (default is direct file access).')
    parser_stdout.add_argument('-f', '--force', action = 'store_true', help = 'Force analyzer to run even if jobs are not all finished.')
    parser_stdout.set_defaults(func = stdout)

    # 'dtk analyze' options
    parser_analyze = subparsers.add_parser('analyze', help = 'Analyze finished simulations in experiment according to analyzers.')
    parser_analyze.add_argument(dest = 'expId', default = None, nargs = '?', help = 'Experiment ID or name.')
    parser_analyze.add_argument(dest = 'config_name', default = None, help = 'Python script for custom analysis of simulations.')
    parser_analyze.add_argument('-c', '--comps', action='store_true', help = 'Use COMPS asset service to read output files (default is direct file access).')
    parser_analyze.add_argument('-f', '--force', action = 'store_true', help = 'Force analyzer to run even if jobs are not all finished.')
    parser_analyze.set_defaults(func = analyze)

    # run specified function passing in function-specific arguments
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
