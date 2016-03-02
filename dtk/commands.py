import argparse
from importlib import import_module
import json
import logging
import os
import sys
import time

import matplotlib.pyplot as plt

import simtools.utils as utils
from simtools.ExperimentManager import ExperimentManagerFactory

from dtk.utils.core.DTKSetupParser import DTKSetupParser


def load_config_module(config_name):
    sys.path.append(os.getcwd())
    module_name = os.path.splitext(os.path.basename(config_name))[0]
    return import_module(module_name)


def run(args):
    # get simulation-running instructions from script
    mod = load_config_module(args.config_name)

    # run the simulation
    location = 'HPC' if (args and args.hpc) else 'LOCAL'
    setup = DTKSetupParser()
    additional_args = {}
    if location == 'HPC':
        if args.priority:
            additional_args['priority'] = args.priority
        if args.node_group:
            additional_args['node_group'] = args.node_group
    sm = ExperimentManagerFactory.from_setup(setup, location, **additional_args)
    sm.run_simulations(**mod.run_sim_args)


def status(args):
    # reload the experiment
    sm = reload_experiment(args)

    # monitor the status of the simulation
    while True:
        states, msgs = sm.get_simulation_status()
        sm.print_status(states, msgs)
        if not args.repeat or sm.status_finished(states):
            break
        else:
            time.sleep(20)


def resubmit(args):
    sm = reload_experiment(args)

    if args.all:
        logging.debug('Resubmitting all failed and canceled jobs in experiment')
        sm.resubmit_simulations(resubmit_all_failed=True)
    elif args.ids:
        logging.info('Resubmitting job(s) with ids: ' + str(args.ids))
        sm.resubmit_simulations(ids=args.ids)
    else:
        logging.ingo("No job IDs were specified.  Run 'dtk resubmit -h' to see options.")


def kill(args):
    sm = reload_experiment(args)

    if args.all:
        logging.debug('Killing all jobs in experiment')
        sm.cancel_simulations(killall=True)
    elif args.ids:
        logging.info('Killing job(s) with ids: ' + str(args.ids))
        sm.cancel_simulations(ids=args.ids)
    else:
        logging.info("No job IDs were specified.  Run 'dtk kill -h' to see options.")


def analyze(args):

    logging.info('Analyzing results...')

    sm = reload_experiment(args)

    if not args.force:
        states, msgs = sm.get_simulation_status()
        if not sm.status_succeeded(states):
            logging.warning('Not all jobs have finished successfully yet...')
            logging.info('Job states:')
            logging.info(json.dumps(states, sort_keys=True, indent=4))
            return

    if args.config_name:
        analyze_from_script(args, sm)
    else:
        logging.info(args.analyzers)
        for analyzer in args.analyzers:
            a = analyzer.split('.')
            if len(a) > 1:
                analyzer_module = import_module('.'.join(['dtk.utils.analyzers'] + a[:-1]))
                analyzer = a[-1]
            else:
                analyzer_module = import_module('dtk.utils.analyzers.' + analyzer)
            analyzer_obj = getattr(analyzer_module, analyzer)()
            sm.add_analyzer(analyzer_obj)

    sm.analyze_simulations()
    plt.show()


def analyze_from_script(args, sim_manager):
    # get simulation-analysis instructions from script
    mod = load_config_module(args.config_name)

    # analyze the simulations
    for analyzer in mod.analyzers:
        sim_manager.add_analyzer(analyzer)


def reload_experiment(args=None):
    if args.expId:
        filepath = utils.exp_file_from_id(args.expId)
    else:
        filepath = utils.most_recent_exp_file()
    return ExperimentManagerFactory.from_file(filepath)


def main():

    parser = argparse.ArgumentParser(prog='dtk')
    subparsers = parser.add_subparsers()

    # 'dtk run' options
    parser_run = subparsers.add_parser('run', help='Run one or more simulations configured by run-options')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of simulation.')
    parser_run.add_argument('--hpc', action='store_true', help='Run simulation on HPC using COMPS (default is local simulation).')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.set_defaults(func=run)

    # 'dtk status' options
    parser_status = subparsers.add_parser('status', help='Report status of simulations in experiment specified by ID')
    parser_status.add_argument('-e', '--expId', dest='expId', default=None, help='Experiment ID identifying JSON file to load back simulation manager.')
    parser_status.add_argument('-r', '--repeat', action='store_true', help='Repeat status check until job is done processing')
    parser_status.set_defaults(func=status)

    # 'dtk resubmit' options
    parser_resubmit = subparsers.add_parser('resubmit', help='Resubmit failed or canceled simulations specified by ID')
    parser_resubmit.add_argument(dest='ids', default=None, nargs='*', type=int, help='Process or job IDs of simulations to resubmit.')
    parser_resubmit.add_argument('-e', '--expId', dest='expId', default=None, help='Experiment ID identifying JSON file to load back simulation manager.')
    parser_resubmit.add_argument('--all', action='store_true', help='Resubmit all failed or canceled simulations in experiment')
    parser_resubmit.set_defaults(func=resubmit)

    # 'dtk kill' options
    parser_kill = subparsers.add_parser('kill', help='Kill running simulations specified by ID')
    parser_kill.add_argument(dest='ids', default=None, nargs='*', help='Process or job IDs of simulations to kill.')
    parser_kill.add_argument('-e', '--expId', dest='expId', default=None, help='Experiment ID identifying JSON file to load back simulation manager.')
    parser_kill.add_argument('--all', action='store_true', help='Kill all simulations in experiment')
    parser_kill.set_defaults(func=kill)

    # 'dtk analyze' options
    parser_analyze = subparsers.add_parser('analyze', help='Analyze finished simulations in experiment according to analyzers')
    parser_analyze.add_argument(dest='config_name', default=None, nargs='?', help='Name of configuration python script for custom analysis of simulations.')
    parser_analyze.add_argument('-e', '--expId', dest='expId', default=None, help='Experiment ID identifying JSON file to load back simulation manager.')
    parser_analyze.add_argument('-a', '--analyzer', dest='analyzers', nargs='*', default=[], help='Analyzers to use on simulations.')
    parser_analyze.add_argument('-f', '--force', action='store_true', help='Force analyzer to run even if jobs are not all finished.')
    parser_analyze.set_defaults(func=analyze)

    # run specified function passing in function-specific arguments
    args = parser.parse_args()
    args.func(args)


if __name__ == '__main__':
    main()
