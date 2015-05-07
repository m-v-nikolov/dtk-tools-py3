import argparse
import copy
from collections import Counter
import glob
from importlib import import_module
import json
import os
import subprocess
import sys
import time

import matplotlib.pyplot as plt

from dtk.utils.core.DTKSetupParser import DTKSetupParser
from dtk.utils.simulation.SimulationManager import SimulationManagerFactory

def load_config_module(config_name):
    sys.path.append(os.getcwd())
    module_name=os.path.splitext(os.path.basename(config_name))[0]
    return import_module(module_name)

def run(args):
    # get simulation-running instructions from script
    mod=load_config_module(args.config_name)
    
    # run the simulation
    location = 'HPC' if (args and args.hpc) else 'HPC-OLD' if (args and args.hpc_old) else 'LOCAL'
    setup = DTKSetupParser()
    sm = SimulationManagerFactory.from_exe(setup.get('BINARIES','exe_path'),location)
    sm.RunSimulations(**mod.run_sim_args)

def status(args):

    # reload the experiment
    sm = reload_experiment(args)

    # monitor the status of the simulation
    while True:
        states, msgs = sm.SimulationStatus()
        sm.printStatus(states,msgs)
        if not args.repeat or sm.statusFinished(states):
            break
        else:
            time.sleep(20)

def resubmit(args):
    sm = reload_experiment(args)
    if args.all:
        #print('Resubmitting all failed and canceled jobs in experiment')
        sm.ResubmitSimulations(resubmit_all_failed=True)
    elif args.ids:
        print('Resubmitting job(s) with ids: ' + str(args.ids))
        sm.ResubmitSimulations(ids=args.ids)
    else:
        print("No job IDs were specified.  Run 'dtk resubmit -h' to see options.")

def kill(args):
    sm = reload_experiment(args)
    if args.all:
        #print('Killing all jobs in experiment')
        sm.CancelSimulations(killall=True)
    elif args.ids:
        print('Killing job(s) with ids: ' + str(args.ids))
        sm.CancelSimulations(ids=args.ids)
    else:
        print("No job IDs were specified.  Run 'dtk kill -h' to see options.")

def analyze(args):

    print('Analyzing results...')

    sm = reload_experiment(args)

    if not args.force:
        states, msgs = sm.SimulationStatus()
        finished = all(v in [ 'Finished', 'Succeeded' ] for v in states.itervalues())
        if not finished:
            print('Not all jobs have finished successfully yet...')
            print('Job states:')
            print( json.dumps(states, sort_keys=True, indent=4) )
            return

    if args.config_name:
        analyze_from_script(args, sm)
    else:
        print(args.analyzers)
        for analyzer in args.analyzers:
            a=analyzer.split('.')
            if len(a) > 1:
                analyzer_module = import_module('.'.join(['dtk.utils.analyzers'] + a[:-1]))
                analyzer=a[-1]
            else:
                analyzer_module = import_module('dtk.utils.analyzers.' + analyzer)
            analyzer_obj = getattr(analyzer_module, analyzer)()
            sm.AddAnalyzer(analyzer_obj)

    sm.AnalyzeSimulations()
    plt.show()

def analyze_from_script(args, sim_manager):

    # get simulation-analysis instructions from script
    mod=load_config_module(args.config_name)

    # analyze the simulations
    for analyzer in mod.analyzers:
        sim_manager.AddAnalyzer(analyzer)

def reload_experiment(args=None):

    if args.expId:
        expfiles = glob.glob('simulations/*' + args.expId + '.json')
        if len(expfiles) == 1:
            filepath = expfiles[0]
        elif len(expfiles) > 1:
            raise Exception('Ambiguous experiment-id; multiple matches found.')
        else:
            raise Exception('Unable to find experiment-id meta-data file for experiment ' + args.expId + '.')
    else:
        print('Getting most recent experiment in current directory...')
        expfiles = glob.glob('simulations/*.json')
        if expfiles:
            filepath = max(expfiles, key=os.path.getctime)
        else:
            raise Exception('Unable to find experiment meta-data file in local directory.')

    return SimulationManagerFactory.from_file(filepath)

def main():

    parser = argparse.ArgumentParser(prog='dtk')
    subparsers = parser.add_subparsers()

    # 'dtk run' options
    parser_run = subparsers.add_parser('run', help='Run one or more simulations configured by run-options')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of simulation.')
    parser_run.add_argument('--hpc', action='store_true', help='Run simulation on HPC using COMPS (default is local simulation).')
    parser_run.add_argument('--hpc-old', action='store_true', help='Run simulation on HPC using "job submit" (deprecated).')
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
