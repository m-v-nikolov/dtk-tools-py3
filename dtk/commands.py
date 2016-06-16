import argparse
from importlib import import_module
import json
import logging
import os
import sys
import time

import npyscreen

import simtools.utils as utils

from dtk.utils.analyzers import ProgressAnalyzer
from dtk.utils.analyzers import StdoutAnalyzer
from dtk.utils.setupui.SetupApplication import SetupApplication
from simtools.ExperimentManager import ExperimentManagerFactory

from simtools.SetupParser import SetupParser

from dtk.utils.analyzers.select import example_selection
from dtk.utils.analyzers.group  import group_by_name
from dtk.utils.analyzers.plot   import plot_grouped_lines
from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer
builtinAnalyzers = { 
    'time_series': TimeseriesAnalyzer(select_function=example_selection(), group_function=group_by_name('_site_'), plot_function=plot_grouped_lines), 
    'vector_species': VectorSpeciesAnalyzer(select_function=example_selection(), group_function=group_by_name('_site_')) 
}

def load_config_module(config_name):
    sys.path.append(os.getcwd())
    module_name = os.path.splitext(os.path.basename(config_name))[0]
    return import_module(module_name)

def setup(args, unknownArgs):
    # If we are on windows, resize the terminal
    if os.name == "nt":
        os.system("mode con: cols=100 lines=35")
    else:
        sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=35, cols=100))

    npyscreen.DISABLE_RESIZE_SYSTEM = True
    SetupApplication().run()

def run(args, unknownArgs):
    # get simulation-running instructions from script
    mod = load_config_module(args.config_name)

    # Get the proper configuration block.
    if len(unknownArgs) == 0:
        selected_block = None
    elif len(unknownArgs) == 1:
        selected_block = unknownArgs[0][2:].upper()
    else:
        raise Exception('Too many unknown arguments: please see help.')

    # run the simulation
    setup = SetupParser(selected_block=selected_block, setup_file=args.ini, force=True)
    additional_args = {}
    if setup.get('type') == 'HPC':
        if args.priority:
            additional_args['priority'] = args.priority
        if args.node_group:
            additional_args['node_group'] = args.node_group

    if args.blocking:
        setup.set('blocking', '1')

    if args.quiet:
        setup.set('quiet', '1')

    # Create the experiment manager based on the setup
    sm = ExperimentManagerFactory.from_setup(setup, location=setup.get('type'), **additional_args)
    sm.run_simulations(**mod.run_sim_args)


def status(args, unknownArgs):
    if args.active:
        logging.info('Getting status of all active experiments.')
        sms = reload_active_experiments()
        for sm in sms:
            states, msgs = sm.get_simulation_status()
            sm.print_status(states, msgs)
        return

    sm = reload_experiment(args)
    while True:
        states, msgs = sm.get_simulation_status(args.repeat)
        sm.print_status(states, msgs)
        if not args.repeat or sm.finished():
            break
        else:
            time.sleep(20)


def resubmit(args, unknownArgs):
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

def kill(args, unknownArgs):

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()
    sm.print_status(states, msgs)

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

def stdout(args, unknownArgs):
    logging.info('Getting stdout...')

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()

    if args.succeeded:
        args.simIds = [k for k in states if states.get(k) in ['Finished', 'Succeeded']][:1]
    elif args.failed:
        args.simIds = [k for k in states if states.get(k) in ['Failed']][:1]

    if not sm.status_succeeded(states):
        logging.warning('WARNING: not all jobs have finished successfully yet...')

    sm.add_analyzer(StdoutAnalyzer(args.simIds, args.error))

    if args.comps:
        utils.override_HPC_settings(sm.setup, use_comps_asset_svc='1')

    sm.analyze_simulations()

def progress(args, unknownArgs):
    logging.info('Getting progress...')

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()

    sm.add_analyzer(ProgressAnalyzer(args.simIds))

    if args.comps:
        utils.override_HPC_settings(sm.setup, use_comps_asset_svc='1')

    sm.analyze_simulations()

def analyze(args, unknownArgs):

    logging.info('Analyzing results...')

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()

    if not args.force:
        if not sm.status_succeeded(states):
            logging.warning('Not all jobs have finished successfully yet...')
            logging.info('Job states:')
            logging.info(json.dumps(states, sort_keys=True, indent=4))
            return
        
    if os.path.exists(args.config_name):
        analyze_from_script(args, sm)
    elif args.config_name in builtinAnalyzers.keys():
        sm.add_analyzer(builtinAnalyzers[args.config_name])
    else:
        logging.error('Unknown analyzer...available builtin analyzers: ' + ', '.join(builtinAnalyzers.keys()))
        return

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
    parser_run.add_argument('--ini', default = None, help = 'Specify an overlay configuration file (*.ini).')
    parser_run.add_argument('--priority', default = None, help = 'Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default = None, help = 'Specify node group of COMPS simulation (only for HPC).')
    parser_run.add_argument('-b', '--blocking', action = 'store_true', help = 'Block the thread until the simulations are done.')
    parser_run.add_argument('-q', '--quiet', action = 'store_true', help = 'Runs quietly.')
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
    parser_stdout = subparsers.add_parser('stdout', help = 'Print stdout from first simulation in selected experiment.')
    parser_stdout.add_argument(dest = 'expId', default = None, nargs = '?', help =' Experiment ID or name.')
    parser_stdout.add_argument('-s', '--simIds', dest = 'simIds', default = None, nargs = '+', help = 'Process or job IDs of simulations to print.')
    parser_stdout.add_argument('-c', '--comps', action='store_true', help = 'Use COMPS asset service to read output files (default is direct file access).')
    parser_stdout.add_argument('-e', '--error', action = 'store_true', help = 'Print stderr instead of stdout.')
    parser_stdout.add_argument('--failed', action = 'store_true', help = 'Get the stdout for the first failed simulation in the selected experiment.')
    parser_stdout.add_argument('--succeeded', action = 'store_true', help = 'Get the stdout for the first succeeded simulation in the selected experiment.')
    parser_stdout.set_defaults(func = stdout)

    # 'dtk progress' options
    parser_progress = subparsers.add_parser('progress', help = 'Print progress from simulation(s) in experiment.')
    parser_progress.add_argument(dest = 'expId', default = None, nargs = '?', help =' Experiment ID or name.')
    parser_progress.add_argument('-s', '--simIds', dest = 'simIds', default = None, nargs = '+', help = 'Process or job IDs of simulations to print.')
    parser_progress.add_argument('-c', '--comps', action='store_true', help = 'Use COMPS asset service to read output files (default is direct file access).')
    parser_progress.set_defaults(func = progress)

    # 'dtk analyze' options
    parser_analyze = subparsers.add_parser('analyze', help = 'Analyze finished simulations in experiment according to analyzers.')
    parser_analyze.add_argument(dest = 'expId', default = None, nargs = '?', help = 'Experiment ID or name.')
    parser_analyze.add_argument(dest = 'config_name', default = None, help = 'Python script for custom analysis of simulations.')
    parser_analyze.add_argument('-c', '--comps', action = 'store_true', help = 'Use COMPS asset service to read output files (default is direct file access).')
    parser_analyze.add_argument('-f', '--force', action = 'store_true', help = 'Force analyzer to run even if jobs are not all finished.')
    parser_analyze.set_defaults(func = analyze)

    # 'dtk setup' options
    parser_setup = subparsers.add_parser('setup', help='Launch the setup UI allowing to edit ini configuration files.')
    parser_setup.set_defaults(func=setup)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()
    args.func(args, unknownArgs)

if __name__ == '__main__':
    main()
