import argparse
import os
# from calibtool import commands_args
from calibtool import commands_args
from simtools.SetupParser import SetupParser
import simtools.Utilities.Initialization as init

def get_calib_manager(args, unknownArgs, force_metadata=False):
    manager = args.loaded_module.calib_manager

    # Update the SetupParser to match the existing experiment environment/block if force_metadata == True
    if force_metadata:
        exp = manager.get_experiment_from_iteration(iteration=args.iteration, force_metadata=force_metadata)
        SetupParser.override_block(exp.selected_block)
    return manager

# ck4, find a nicer way to auto-detect available methods? e.g. put such methods in a single place for discovery?
RESAMPLE_METHODS = ['cramer-rao']

def run(args, unknownArgs):
    from calibtool import CalibManager
    import dtk.commands

    if args.resample:
        if not args.analyzer:
            raise Exception('-a must be used with if -r is specified.')
        if args.resample not in RESAMPLE_METHODS:
            raise Exception('Unknown resampling method: %s . Allowed resampling methods: %s .' %
                            args.resample, ' , '.join(RESAMPLE_METHODS))

    manager = get_calib_manager(args, unknownArgs)
    manager.run_calibration()

    # do resampling process
    if args.resample:
        calibrated_point = manager.get_calibrated_point()

        # step 1: resample via gaussian in the vicinity of the calibrated point
        # resampled_points is a list of ParameterConfiguration objects. Need to define the ParameterConfiguration class, ck4
        resampled_points = manager.resample(method=CalibManager.GAUSSIAN)

        # step 2: run simulations at these points
        # step 2a: set arguments on the args Namespace
        args.stuff = 'resampled_points_in_here' # ck4
        dtk.commands.run(args, unknownArgs)

        # step 3: analyze to get liklihoods
        # step 3a: set arguments on the args Namespace
        args.stuff = 'resampled_points_in_here' # ck4
        dtk.commands.analyze(args, unknownArgs)

        # step 4: resample according to the requested methodology
        # resampled_points is a list of ParameterConfiguration objects. Need to define the ParameterConfiguration class, ck4
        resampled_points = manager.resample(method=args.resample)

        # step 5: write out the resampled points for later use
        # The results file, 'somefilename.csv' will be usable in a 'dtk run' script for generating a sweep
        # via some provided hook, like: ParameterConfigurationSet.load(filename='somefilename.csv').sweep_items()
        ParameterConfigurationSet(points=resampled_points).write(filename='somefilename.csv')

def resume(args, unknownArgs):
    if args.iter_step:
        if args.iter_step not in ['commission', 'analyze', 'plot', 'next_point']:
            print("Invalid iter_step '%s', ignored." % args.iter_step)
            exit()
    manager = get_calib_manager(args, unknownArgs, force_metadata=True)
    manager.resume_calibration(args.iteration, iter_step=args.iter_step)


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


def main():
    parser = argparse.ArgumentParser(prog='calibtool')
    subparsers = parser.add_subparsers()

    # 'calibtool run' options
    commands_args.populate_run_arguments(subparsers, run)

    # 'calibtool resume' options
    commands_args.populate_resume_arguments(subparsers, resume)

    # 'calibtool cleanup' options
    commands_args.populate_cleanup_arguments(subparsers, cleanup)

    # 'calibtool kill' options
    commands_args.populate_kill_arguments(subparsers, kill)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()
    # This is it! This is where SetupParser gets set once and for all. Until you run 'dtk COMMAND' again, that is.
    init.initialize_SetupParser_from_args(args, unknownArgs)
    args.func(args, unknownArgs)

if __name__ == '__main__':
    main()
