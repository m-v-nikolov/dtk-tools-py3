import argparse
from importlib import import_module
import os
import sys

from simtools.SetupParser import SetupParser


def load_config_module(config_name):
    config_name = config_name.replace('\\', '/')
    if '/' in config_name:
        splitted = config_name.split('/')[:-1]
        sys.path.append(os.path.join(os.getcwd(), *splitted))
    else:
        sys.path.append(os.getcwd())

    module_name = os.path.splitext(os.path.basename(config_name))[0]
    return import_module(module_name)


def get_calib_manager_args(args, unknownArgs):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    calib_args = mod.run_calib_args

    manager_data = manager.read_calib_data(True)
    calib_args['block'] = manager_data['selected_block'] if manager_data else None
    calib_args['ini'] = manager_data['setup_overlay_file'] if manager_data else None
    update_calib_args(args, unknownArgs, calib_args)
    return manager, calib_args


def update_calib_args(args, unknownArgs, calib_args):
    if args.priority:
        calib_args['priority'] = args.priority
    if args.node_group:
        calib_args['node_group'] = args.node_group

    # Get the proper configuration block.
    if len(unknownArgs) == 0:
        selected_block = calib_args['block']
    elif len(unknownArgs) == 1:
        selected_block = unknownArgs[0][2:].upper()
    else:
        raise Exception('Too many unknown arguments: please see help.')

    # Update the setupparser
    SetupParser(selected_block=selected_block, setup_file=args.ini if args.ini else calib_args['ini'], force=True)


def run(args, unknownArgs):
    manager, calib_args = get_calib_manager_args(args, unknownArgs)
    manager.run_calibration(**calib_args)


def resume(args, unknownArgs):
    manager, calib_args = get_calib_manager_args(args,unknownArgs)
    manager.resume_from_iteration(args.iteration,
                                  iter_step=args.iter_step,
                                  **calib_args)


def reanalyze(args, unknownArgs):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    manager.reanalyze()


def cleanup(args, unknownArgs):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    # If no result present -> just exit
    if not os.path.exists(os.path.join(os.getcwd(), manager.name)):
        print 'No calibration to delete. Exiting...'
        exit()
    manager.cleanup()


def kill(args, unknownArgs):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    manager.kill()


def replot(args, unknownArgs):
    mod = load_config_module(args.config_name)
    manager = mod.calib_manager
    run_calib_args = mod.run_calib_args

    # Consider delete-only option
    if len(unknownArgs) == 0:
        run_calib_args['delete'] = None
    elif len(unknownArgs) == 1:
        run_calib_args['delete'] = unknownArgs[0][2:].upper()
    else:
        raise Exception('Too many unknown arguments: please see help.')

    manager.replot_calibration(**run_calib_args)


def main():

    parser = argparse.ArgumentParser(prog='calibtool')
    subparsers = parser.add_subparsers()

    # 'calibtool run' options
    parser_run = subparsers.add_parser('run', help='Run a calibration configured by run-options')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_run.add_argument('--ini', default=None, help='Specify an overlay configuration file (*.ini).')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.set_defaults(func=run)

    # 'calibtool resume' options
    parser_resume = subparsers.add_parser('resume', help='Resume a calibration configured by resume-options')
    parser_resume.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_resume.add_argument('--iteration', default=None, type=int, help='Resume calibration from iteration number (default is last cached state).')
    parser_resume.add_argument('--iter_step', default=None, help="Resume calibration on specified iteration step ['commission', 'analyze', 'next_point'].")
    parser_resume.add_argument('--ini', default=None, help='Specify an overlay configuration file (*.ini).')
    parser_resume.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_resume.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_resume.set_defaults(func=resume)

    # 'calibtool reanalyze' options
    parser_reanalyze = subparsers.add_parser('reanalyze', help='Rerun the analyzers of a calibration')
    parser_reanalyze.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_reanalyze.set_defaults(func=reanalyze)

    # 'calibtool cleanup' options
    parser_cleanup = subparsers.add_parser('cleanup', help='Cleanup a calibration')
    parser_cleanup.add_argument(dest='config_name', default=None,
                               help='Name of configuration python script for custom running of calibration.')
    parser_cleanup.set_defaults(func=cleanup)

    # 'calibtool kill' options
    parser_cleanup = subparsers.add_parser('kill', help='Kill a calibration')
    parser_cleanup.add_argument(dest='config_name', default=None,
                               help='Name of configuration python script.')
    parser_cleanup.set_defaults(func=kill)

    # 'calibtool plotter' options
    parser_resume = subparsers.add_parser('replot', help='Re-plot a calibration configured by plotter-options')
    parser_resume.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_resume.set_defaults(func=replot)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()
    args.func(args, unknownArgs)

if __name__ == '__main__':
    main()
