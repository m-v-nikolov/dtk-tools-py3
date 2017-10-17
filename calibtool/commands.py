import argparse
import os

from simtools.SetupParser import SetupParser
import simtools.Utilities.Initialization as init

def get_calib_manager(args, unknownArgs, force_metadata=False):
    manager = args.loaded_module.calib_manager

    # Update the SetupParser to match the existing experiment environment/block if force_metadata == True
    if force_metadata:
        exp = manager.get_experiment_from_iteration(iteration=args.iteration, force_metadata=force_metadata)
        SetupParser.override_block(exp.selected_block)
    return manager

def run(args, unknownArgs):
    manager = get_calib_manager(args, unknownArgs)
    manager.run_calibration()

def resume(args, unknownArgs):
    if args.iter_step:
        if args.iter_step not in ['commission', 'analyze', 'plot', 'next_point']:
            print("Invalid iter_step '%s', ignored." % args.iter_step)
            exit()
    manager = get_calib_manager(args, unknownArgs, force_metadata=True)
    manager.resume_calibration(args.iteration, iter_step=args.iter_step)

def reanalyze(args, unknownArgs):
    manager = get_calib_manager(args, unknownArgs, force_metadata=True)
    manager.reanalyze_calibration(args.iteration)

def cleanup(args, unknownArgs):
    manager = args.loaded_module.calib_manager
    # If no result present -> just exit
    if not os.path.exists(os.path.join(os.getcwd(), manager.name)):
        print('No calibration to delete. Exiting...')
        exit()
    manager.cleanup()

def kill(args, unknownArgs):
    manager = args.loaded_module.calib_manager
    manager.kill()

def replot(args, unknownArgs):
    manager = get_calib_manager(args, unknownArgs, force_metadata=True)
    manager.replot_calibration(args.iteration)

def main():
    parser = argparse.ArgumentParser(prog='calibtool')
    subparsers = parser.add_subparsers()

    # 'calibtool run' options
    parser_run = subparsers.add_parser('run', help='Run a calibration configured by run-options')
    parser_run.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.set_defaults(func=run)

    # 'calibtool resume' options
    parser_resume = subparsers.add_parser('resume', help='Resume a calibration configured by resume-options')
    parser_resume.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_resume.add_argument('--iteration', default=None, type=int, help='Resume calibration from iteration number (default is last cached state).')
    parser_resume.add_argument('--iter_step', default=None, help="Resume calibration on specified iteration step ['commission', 'analyze', 'plot', 'next_point'].")
    parser_resume.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_resume.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_resume.set_defaults(func=resume)

    # 'calibtool reanalyze' options
    parser_reanalyze = subparsers.add_parser('reanalyze', help='Rerun the analyzers of a calibration')
    parser_reanalyze.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_reanalyze.add_argument('--iteration', default=None, type=int, help='Resume calibration from iteration number (default is last cached state).')
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
    parser_replot = subparsers.add_parser('replot', help='Re-plot a calibration configured by plotter-options')
    parser_replot.add_argument(dest='config_name', default=None, help='Name of configuration python script for custom running of calibration.')
    parser_replot.add_argument('--iteration', default=None, type=int, help='Replot calibration for one iteration (default is to iterate over all).')
    parser_replot.set_defaults(func=replot)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()
    # This is it! This is where SetupParser gets set once and for all. Until you run 'dtk COMMAND' again, that is.
    init.initialize_SetupParser_from_args(args, unknownArgs)
    args.func(args, unknownArgs)

if __name__ == '__main__':
    main()
