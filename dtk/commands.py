import argparse
import json
import logging
import os
import subprocess
import sys
from importlib import import_module

import datetime
import simtools.utils as utils
from dtk.utils.analyzers import ProgressAnalyzer
from dtk.utils.analyzers import StdoutAnalyzer
from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer
from dtk.utils.analyzers.group import group_by_name
from dtk.utils.analyzers.plot import plot_grouped_lines
from dtk.utils.analyzers.select import example_selection
from dtk.utils.setupui.SetupApplication import SetupApplication
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser

builtinAnalyzers = {
    'time_series': TimeseriesAnalyzer(select_function=example_selection(), group_function=group_by_name('_site_'),
                                      plot_function=plot_grouped_lines),
    'vector_species': VectorSpeciesAnalyzer(select_function=example_selection(), group_function=group_by_name('_site_'))
}


class objectview(object):
    def __init__(self, d):
        self.__dict__ = d


def load_config_module(config_name):
    # Support of relative paths
    config_name = config_name.replace('\\', '/')
    if '/' in config_name:
        splitted = config_name.split('/')[:-1]
        sys.path.append(os.path.join(os.getcwd(), *splitted))
    else:
        sys.path.append(os.getcwd())

    module_name = os.path.splitext(os.path.basename(config_name))[0]

    try:
        return import_module(module_name)
    except ImportError:
        logging.error("Unable to find %s in %s. Exiting..." % (module_name, os.getcwd()))
        exit()

def test(args, unknownArgs):
    # Get to the test dir
    current_dir = os.path.dirname(os.path.realpath(__file__))
    test_dir = os.path.abspath(os.path.join(current_dir, '..', 'test'))

    # Create the test command
    command = ['nosetests']
    command.extend(unknownArgs)

    # Run
    subprocess.Popen(command, cwd=test_dir).wait()


def setup(args, unknownArgs):
    if os.name == "nt":
        # Get the current console size
        output = subprocess.check_output("mode con", shell=True)
        original_cols = output.split('\n')[3].split(':')[1].lstrip()
        original_rows = output.split('\n')[4].split(':')[1].lstrip()

        # Resize only if needed
        if int(original_cols) < 300 or int(original_rows) < 110:
            os.system("mode con: cols=100 lines=35")
    else:
        sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=35, cols=100))

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

    # Parse setup.
    setup = SetupParser(selected_block=selected_block, setup_file=args.ini, force=True)

    # Assess arguments.
    if args.analyzer:
        args.blocking = True
    if args.blocking:
        setup.set('blocking', '1')
    if args.quiet:
        setup.set('quiet', '1')

    additional_args = {}
    if setup.get('type') == 'HPC':
        if args.priority:
            additional_args['priority'] = args.priority
        if args.node_group:
            additional_args['node_group'] = args.node_group

    # Create the experiment manager based on the setup and run simulation.
    sm = ExperimentManagerFactory.from_setup(setup, location=setup.get('type'), **additional_args)
    sm.run_simulations(**mod.run_sim_args)

    # Perform analyze, if requested.
    if args.analyzer:
        analyze(objectview({'expId': None, 'config_name': args.analyzer, 'force': False, 'comps': True}), None);


def status(args, unknownArgs):
    if args.active:
        logging.info('Getting status of all active experiments.')
        active_experiments = DataStore.get_active_experiments()

        for exp in active_experiments:
            sm = ExperimentManagerFactory.from_experiment(exp)
            states, msgs = sm.get_simulation_status()
            sm.print_status(states, msgs)
        return

    sm = reload_experiment(args)
    if args.repeat:
        sm.wait_for_finished(verbose=True, sleep_time=20)
    else:
        states, msgs = sm.get_simulation_status()
        sm.print_status(states, msgs)


def resubmit(args, unknownArgs):
    sm = reload_experiment(args)

    if args.simIds:
        logging.info('Resubmitting job(s) with ids: ' + str(args.simIds))
        params = {'ids': args.simIds}
    else:
        logging.info('No job IDs were specified.  Resubmitting all failed and canceled jobs in experiment.')
        params = {'resubmit_all_failed': True}

    if args.all:
        sms = reload_experiments(args)
        for sm in sms:
            sm.resubmit_simulations(**params)
    else:
        sm = reload_experiment(args)
        sm.resubmit_simulations(**params)


def kill(args, unknownArgs):
    with utils.nostdout():
        sm = reload_experiment(args)

    logging.info("Killing Experiment %s" % sm.experiment.id)
    states, msgs = sm.get_simulation_status()
    sm.print_status(states, msgs, verbose=False)

    if sm.status_finished(states):
        logging.warn(
            "The Experiment %s is already finished and therefore cannot be killed. Exiting..." % sm.experiment.id)
        return

    if args.simIds:
        logging.info('KIlling job(s) with ids: ' + str(args.simIds))
        params = {'ids': args.simIds}
    else:
        logging.info('No job IDs were specified.  Killing all jobs in selected experiment (or most recent).')
        params = {'killall': True}

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logging.info('No action taken.')
        return

    sm.cancel_simulations(**params)


def exterminate(args, unknownArgs):
    with utils.nostdout():
        sms = reload_experiments(args)

    if args.expId:
        for sm in sms:
            states, msgs = sm.get_simulation_status()
            sm.print_status(states, msgs)
        logging.info('Killing ALL experiments matched by ""' + args.expId + '".')
    else:
        logging.info('Killing ALL experiments.')

    logging.info('%s experiments found.' % len(sms))

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logging.info('No action taken.')
        return

    for sm in sms:
        states, msgs = sm.get_simulation_status()
        sm.cancel_simulations(killall=True)


def delete(args, unknownArgs):
    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()
    sm.print_status(states, msgs)

    if args.hard:
        logging.info('Hard deleting selected experiment.')
    else:
        logging.info('Deleting selected experiment.')

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logging.info('No action taken.')
        return

    if args.hard:
        sm.hard_delete()
    else:
        sm.soft_delete()


def clean(args, unknownArgs):
    with utils.nostdout():
        # Store the current directory to let the reload knows that we want to
        # only retrieve simulations in this directory
        args.current_dir = os.getcwd()
        sms = reload_experiments(args)

    if len(sms) == 0:
        logging.warn("No experiments matched by '%s'. Exiting..." % args.expId)
        return

    if args.expId:
        logging.info("Hard deleting ALL experiments matched by '%s' ran from the current directory.\n%s experiments total." % (args.expId, len(sms)))
        for sm in sms:
            logging.info(sm.experiment)
            states, msgs = sm.get_simulation_status()
            sm.print_status(states, msgs, verbose=False)
            logging.info("")
    else:
        logging.info("Hard deleting ALL experiments ran from the current directory.\n%s experiments total." % len(sms))

    choice = raw_input("Are you sure you want to continue with the selected action (Y/n)? ")

    if choice != "Y":
        logging.info("No action taken.")
        return

    for sm in sms:
        logging.info("Deleting %s" % sm.experiment)
        sm.hard_delete()


def stdout(args, unknownArgs):
    logging.info('Getting stdout...')

    sm = reload_experiment(args)
    states, msgs = sm.get_simulation_status()

    if args.succeeded:
        args.simIds = [k for k in states if states.get(k) in ['Succeeded']][:1]
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


def analyze_list(args, unknownArgs):
    logging.error('\n' + '\n'.join(builtinAnalyzers.keys()))

def sync(args, unknownArgs):
    # Create a default HPC setup parser
    sp = SetupParser('HPC')
    utils.COMPS_login(sp.get('server_endpoint'))
    from COMPS.Data import Experiment, Suite, QueryCriteria

    exp_to_save = list()
    exp_deleted = 0

    # Test the experiments present in the local DB to make sure they still exist in COMPS
    for exp in DataStore.get_experiments(None):
        if exp.location == "HPC":
            if len(Experiment.Get(QueryCriteria().Where("Id=%s" % exp.exp_id)).toArray()) == 0:
                # The experiment doesnt exist on COMPS anymore -> delete from local
                DataStore.delete_experiment(exp)
                exp_deleted+=1

    # By default only get simulations created in the last month
    today = datetime.date.today()
    limit_date = today - datetime.timedelta(days=30)
    limit_date_str = limit_date.strftime("%Y-%m-%d")

    exps = Experiment.Get(QueryCriteria().Where('Owner=%s,DateCreated>%s' % (sp.get('user'), limit_date_str))).toArray()

    # For each of them, check if they are in the db
    for exp in exps:
        with utils.nostdout():
            experiment = DataStore.get_experiment(exp.getId().toString())
            if experiment and experiment.is_done(): continue # Do not bother with finished experiments
        if not experiment:
            # Cast the creation_date
            creation_date = datetime.datetime.strptime(exp.getDateCreated().toString(), "%a %b %d %H:%M:%S PDT %Y")
            experiment = DataStore.create_experiment(exp_id=exp.getId().toString(),
                                                     suite_id=exp.getSuiteId().toString() if exp.getSuiteId() else None,
                                                     exp_name=exp.getName(),
                                                     date_created=creation_date,
                                                     location='HPC',
                                                     selected_block='HPC',
                                                     endpoint=sp.get('server_endpoint'),
                                                     working_directory=os.getcwd())

        sims = exp.GetSimulations(QueryCriteria().Select('Id,SimulationState,DateCreated').SelectChildren('Tags')).toArray()

        # Skip empty experiments or experiments that have the same number of sims
        if len(sims) == 0 or len(sims) == len(experiment.simulations): continue

        # Go through the sims and create them
        for sim in sims:
            # Create the tag dict
            tags = dict()
            for key in sim.getTags().keySet().toArray():
                tags[key] = sim.getTags().get(key)

            # Prepare the date
            creation_date = datetime.datetime.strptime(sim.getDateCreated().toString(), "%a %b %d %H:%M:%S PDT %Y")

            # Create the simulation
            simulation = DataStore.create_simulation(id=sim.getId().toString(),
                                                     status=sim.getState().toString(),
                                                     tags=tags,
                                                     date_created=creation_date)
            # Add to the experiment
            experiment.simulations.append(simulation)

        # The experiment needs to be saved
        exp_to_save.append(experiment)

    # Save the experiments if any
    if len(exp_to_save) > 0 and exp_deleted == 0:
        DataStore.batch_save_experiments(exp_to_save)
        logging.info("%s experiments have been updated in the DB." % len(exp_to_save))
        logging.info("%s experiments have been deleted from the DB." % exp_deleted)
    else:
        logging.info("The database was already up to date.")


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

    return ExperimentManagerFactory.from_experiment(DataStore.get_most_recent_experiment(id))


def reload_experiments(args=None):
    if args:
        id = args.expId
    else:
        id = None

    current_dir = args.current_dir if 'current_dir' in args else None

    return map(lambda exp: ExperimentManagerFactory.from_experiment(exp), DataStore.get_experiments(id, current_dir))


def main():
    parser = argparse.ArgumentParser(prog='dtk')
    subparsers = parser.add_subparsers()

    # 'dtk run' options
    parser_run = subparsers.add_parser('run', help='Run one or more simulations configured by run-options.')
    parser_run.add_argument(dest='config_name', default=None,
                            help='Name of configuration python script for custom running of simulation.')
    parser_run.add_argument('--ini', default=None, help='Specify an overlay configuration file (*.ini).')
    parser_run.add_argument('--priority', default=None, help='Specify priority of COMPS simulation (only for HPC).')
    parser_run.add_argument('--node_group', default=None, help='Specify node group of COMPS simulation (only for HPC).')
    parser_run.add_argument('-b', '--blocking', action='store_true',
                            help='Block the thread until the simulations are done.')
    parser_run.add_argument('-q', '--quiet', action='store_true', help='Runs quietly.')
    parser_run.add_argument('-a', '--analyzer', default=None,
                            help='Specify an analyzer name or configuartion to run upon completion (this operation is blocking).')
    parser_run.set_defaults(func=run)

    # 'dtk status' options
    parser_status = subparsers.add_parser('status',
                                          help='Report status of simulations in experiment specified by ID or name.')
    parser_status.add_argument(dest='expId', default=None, nargs='?', help='Experiment ID or name.')
    parser_status.add_argument('-r', '--repeat', action='store_true',
                               help='Repeat status check until job is done processing.')
    parser_status.add_argument('-a', '--active', action='store_true',
                               help='Get the status of all active experiments (mutually exclusive to all other options).')
    parser_status.set_defaults(func=status)

    # 'dtk resubmit' options
    parser_resubmit = subparsers.add_parser('resubmit',
                                            help='Resubmit failed or canceled simulations specified by experiment ID or name.')
    parser_resubmit.add_argument(dest='expId', default=None, nargs='?', help='Experiment ID or name.')
    parser_resubmit.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+',
                                 help='Process or job IDs of simulations to resubmit.')
    parser_resubmit.add_argument('-a', '--all', action='store_true',
                                 help='Resubmit all failed or canceled simulations in selected experiments.')
    parser_resubmit.set_defaults(func=resubmit)

    # 'dtk kill' options
    parser_kill = subparsers.add_parser('kill', help='Kill most recent running experiment specified by ID or name.')
    parser_kill.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_kill.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+',
                             help='Process or job IDs of simulations to kill.')
    parser_kill.set_defaults(func=kill)

    # 'dtk exterminate' options
    parser_exterminate = subparsers.add_parser('exterminate', help='Kill ALL experiments matched by ID or name.')
    parser_exterminate.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_exterminate.set_defaults(func=exterminate)

    # 'dtk delete' options
    parser_delete = subparsers.add_parser('delete',
                                          help='Delete most recent experiment (tracking objects only, e.g., local cache) specified by ID or name.')
    parser_delete.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_delete.add_argument('--hard', action='store_true',
                               help='Additionally delete working directory or server entities for experiment.')
    parser_delete.set_defaults(func=delete)

    # 'dtk clean' options
    parser_clean = subparsers.add_parser('clean', help='Hard deletes ALL experiments in {current_dir}\simulations matched by ID or name.')
    parser_clean.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_clean.set_defaults(func=clean)

    # 'dtk stdout' options
    parser_stdout = subparsers.add_parser('stdout', help='Print stdout from first simulation in selected experiment.')
    parser_stdout.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_stdout.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+',
                               help='Process or job IDs of simulations to print.')
    parser_stdout.add_argument('-c', '--comps', action='store_true',
                               help='Use COMPS asset service to read output files (default is direct file access).')
    parser_stdout.add_argument('-e', '--error', action='store_true', help='Print stderr instead of stdout.')
    parser_stdout.add_argument('--failed', action='store_true',
                               help='Get the stdout for the first failed simulation in the selected experiment.')
    parser_stdout.add_argument('--succeeded', action='store_true',
                               help='Get the stdout for the first succeeded simulation in the selected experiment.')
    parser_stdout.set_defaults(func=stdout)

    # 'dtk progress' options
    parser_progress = subparsers.add_parser('progress', help='Print progress from simulation(s) in experiment.')
    parser_progress.add_argument(dest='expId', default=None, nargs='?', help=' Experiment ID or name.')
    parser_progress.add_argument('-s', '--simIds', dest='simIds', default=None, nargs='+',
                                 help='Process or job IDs of simulations to print.')
    parser_progress.add_argument('-c', '--comps', action='store_true',
                                 help='Use COMPS asset service to read output files (default is direct file access).')
    parser_progress.set_defaults(func=progress)

    # 'dtk analyze' options
    parser_analyze = subparsers.add_parser('analyze',
                                           help='Analyze finished simulations in experiment according to analyzers.')
    parser_analyze.add_argument(dest='expId', default=None, nargs='?', help='Experiment ID or name.')
    parser_analyze.add_argument(dest='config_name', default=None,
                                help='Python script or builtin analyzer name for custom analysis of simulations.')
    parser_analyze.add_argument('-c', '--comps', action='store_true',
                                help='Use COMPS asset service to read output files (default is direct file access).')
    parser_analyze.add_argument('-f', '--force', action='store_true',
                                help='Force analyzer to run even if jobs are not all finished.')
    parser_analyze.set_defaults(func=analyze)

    # 'dtk analyze-list' options
    parser_analyze_list = subparsers.add_parser('analyze-list', help='List the available builtin analyzers.')
    parser_analyze_list.set_defaults(func=analyze_list)

    parser_analyze_list = subparsers.add_parser('sync', help='Synchronize the COMPS database with the local database.')
    parser_analyze_list.set_defaults(func=sync)

    # 'dtk setup' options
    parser_setup = subparsers.add_parser('setup', help='Launch the setup UI allowing to edit ini configuration files.')
    parser_setup.set_defaults(func=setup)

    # 'dtk test' options
    parser_test = subparsers.add_parser('test', help='Launch the nosetests on the test folder.')
    parser_test.set_defaults(func=test)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()
    args.func(args, unknownArgs)


if __name__ == '__main__':
    main()
