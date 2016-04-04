import argparse
from importlib import import_module
import os
import sys


def load_config_module(config_name):
    sys.path.append(os.getcwd())
    module_name = os.path.splitext(os.path.basename(config_name))[0]
    return import_module(module_name)


def get_calib_manager_args(args):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    calib_args = mod.run_calib_args
    update_calib_args(args, calib_args)
    return manager, calib_args


def update_calib_args(args, calib_args):
    location = 'HPC' if (args and args.hpc) else 'LOCAL'
    calib_args['location'] = location
    if args.priority:
        calib_args['priority'] = args.priority
    if args.node_group:
        calib_args['node_group'] = args.node_group


def run(args):

    manager, calib_args = get_calib_manager_args(args)
    manager.run_calibration(**calib_args)


def resume(args):
    manager, calib_args = get_calib_manager_args(args)
    manager.resume_from_iteration(args.iteration,
                                  iter_step=args.iter_step,
                                  **calib_args)

def reanalyze(args):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    manager.reanalyze()

def cleanup(args):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    manager.cleanup()

def main():

    parser = argparse.ArgumentParser(prog='calibtool')
    subparsers = parser.add_subparsers()

    # 'calibtool run' options
    parser_run = subparsers.add_parser('run', help='Run a calibration configured by run-options')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_run.add_argument('--hpc', action='store_true', help='Run calibration simulations on HPC using COMPS (default is local simulation).')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.set_defaults(func=run)

    # 'calibtool resume' options
    parser_resume = subparsers.add_parser('resume', help='Resume a calibration configured by resume-options')
    parser_resume.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_resume.add_argument('--iteration', default=None, type=int, help='Resume calibration from iteration number (default is last cached state).')
    parser_resume.add_argument('--iter_step', default=None, help="Resume calibration on specified iteration step ['commission', 'analyze', 'next_point'].")
    parser_resume.add_argument('--hpc', action='store_true', help='Resume calibration simulations on HPC using COMPS (default is local simulation).')
    parser_resume.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_resume.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')

    # 'calibtool reanalyze' options
    parser_reanalyze = subparsers.add_parser('reanalyze', help='Rerun the analyzers of a calibration')
    parser_reanalyze.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_reanalyze.set_defaults(func=reanalyze)

    # 'calibtool cleanup' options
    parser_cleanup = subparsers.add_parser('cleanup', help='Cleanup a calibration')
    parser_cleanup.add_argument(dest='config_name', default=None,
                               help='Name of configuration python script for custom running of calibration.')
    parser_cleanup.set_defaults(func=cleanup)


    # run specified function passing in function-specific arguments
    args = parser.parse_args()
    args.func(args)

if __name__ == '__main__':
    main()
