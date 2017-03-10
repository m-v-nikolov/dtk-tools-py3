import argparse
import csv
import datetime
import os
import subprocess
import sys
from importlib import import_module

import simtools.AnalyzeManager.AnalyzeHelper as AnalyzeHelper
from dtk.HIV.analyzers import *
from dtk.utils.analyzers import ProgressAnalyzer, sample_selection
from dtk.utils.analyzers import StdoutAnalyzer
from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer
from dtk.utils.analyzers.group import group_by_name
from dtk.utils.analyzers.plot import plot_grouped_lines
from dtk.utils.setupui.SetupApplication import SetupApplication
from simtools.DataAccess.DataStore import DataStore
from simtools.DataAccess.LoggingDataStore import LoggingDataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import get_experiments_per_user_and_date, get_experiment_by_id, \
    get_experiments_by_name, COMPS_login
from simtools.Utilities.Experiments import COMPS_experiment_to_local_db, retrieve_experiment
from simtools.Utilities.General import nostdout, override_HPC_settings, get_tools_revision, init_logging

logger = init_logging('Commands')

builtinAnalyzers = {
    'time_series': TimeseriesAnalyzer(select_function=sample_selection(), group_function=group_by_name('_site_'),
                                      plot_function=plot_grouped_lines),
    'vector_species': VectorSpeciesAnalyzer(select_function=sample_selection(), group_function=group_by_name('_site_')),
    'hiv_ReportHIVByAgeAndGender': ReportHIVByAgeAndGenderAnalyzer(force_apply=True, force_combine=True, verbose=True),
    'hiv_RelationshipDuration': RelationshipDurationAnalyzer(),
    'hiv_HIVDebutAnalyzer': RelationshipDurationAnalyzer(),
    'hiv_DebutAgeAnalyzer': DebutAgeAnalyzer(),
    'hiv_PrognosisAnalyzer': PrognosisAnalyzer(),
    'hiv_CircumcisionAnalyzer': CircumcisionAnalyzer(),
    'hiv_CD4ProgressionAnalyzer': CD4ProgressionAnalyzer(),
    'hiv_WHOStageAnalyzer': WHOStageAnalyzer()
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
    except ImportError as e:
        logger.error("ImportError: '%s' during loading module '%s' in %s. Exiting...",
                     e.message, module_name, os.getcwd())
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


def setup2(args, unknownArgs):
    """
    Backup of setupui
    """
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

# def setup(args, unknownArgs):
#     """
#     New Setup Configuraiton Editor
#     """
#     if os.name == "nt":
#         # Get the current console size
#         output = subprocess.check_output("mode con", shell=True)
#         original_cols = output.split('\n')[3].split(':')[1].lstrip()
#         original_rows = output.split('\n')[4].split(':')[1].lstrip()
#
#         # Resize only if needed
#         if int(original_cols) < 300 or int(original_rows) < 110:
#             os.system("mode con: cols=100 lines=35")
#     else:
#         sys.stdout.write("\x1b[8;{rows};{cols}t".format(rows=35, cols=100))
#
#     SetupApplication2().run()


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
    exp_manager = ExperimentManagerFactory.from_setup(setup, **additional_args)
    exp_manager.run_simulations(**mod.run_sim_args)


def status(args, unknownArgs):
    # No matter what check the overseer
    from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
    BaseExperimentManager.check_overseer()

    if args.active:
        logger.info('Getting status of all active experiments.')
        active_experiments = DataStore.get_active_experiments()

        for exp in active_experiments:
            exp_manager = ExperimentManagerFactory.from_experiment(exp)
            states, msgs = exp_manager.get_simulation_status()
            exp_manager.print_status(states, msgs)
        return

    exp_manager = reload_experiment(args)
    if args.repeat:
        exp_manager.wait_for_finished(verbose=True, sleep_time=20)
    else:
        states, msgs = exp_manager.get_simulation_status()
        exp_manager.print_status(states, msgs)


def kill(args, unknownArgs):
    with nostdout():
        exp_manager = reload_experiment(args)

    logger.info("Killing Experiment %s" % exp_manager.experiment.id)
    states, msgs = exp_manager.get_simulation_status()
    exp_manager.print_status(states, msgs, verbose=False)

    if exp_manager.status_finished(states):
        logger.warn(
            "The Experiment %s is already finished and therefore cannot be killed. Exiting..." % exp_manager.experiment.id)
        return

    if args.simIds:
        logger.info('Killing job(s) with ids: ' + str(args.simIds))
    else:
        logger.info('No job IDs were specified.  Killing all jobs in selected experiment (or most recent).')

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logger.info('No action taken.')
        return

    exp_manager.kill(args, unknownArgs)
    print "'Kill' has been executed successfully."


def exterminate(args, unknownArgs):
    with nostdout():
        exp_managers = reload_experiments(args)

    if args.expId:
        for exp_manager in exp_managers:
            states, msgs = exp_manager.get_simulation_status()
            exp_manager.print_status(states, msgs)
        logger.info('Killing ALL experiments matched by ""' + args.expId + '".')
    else:
        logger.info('Killing ALL experiments.')

    logger.info('%s experiments found.' % len(exp_managers))

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logger.info('No action taken.')
        return

    for exp_manager in exp_managers:
        exp_manager.cancel_experiment()

    print "'Exterminate' has been executed successfully."


def delete(args, unknownArgs):
    exp_manager = reload_experiment(args)
    if exp_manager is None:
        logger.info("The experiment doesn't exist. No action executed.")
        return

    states, msgs = exp_manager.get_simulation_status()
    exp_manager.print_status(states, msgs)

    if args.hard:
        logger.info('Hard deleting selected experiment.')
    else:
        logger.info('Deleting selected experiment.')

    choice = raw_input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logger.info('No action taken.')
        return

    exp_manager.delete_experiment(args.hard)
    logger.info("Experiment '%s' has been successfully deleted.", exp_manager.experiment.exp_id)


def clean(args, unknownArgs):
    with nostdout():
        # Store the current directory to let the reload knows that we want to
        # only retrieve simulations in this directory
        args.current_dir = os.getcwd()
        exp_managers = reload_experiments(args)

    if len(exp_managers) == 0:
        logger.warn("No experiments matched by '%s'. Exiting..." % args.expId)
        return

    if args.expId:
        logger.info("Hard deleting ALL experiments matched by '%s' ran from the current directory.\n%s experiments total." % (args.expId, len(exp_managers)))
        for exp_manager in exp_managers:
            logger.info(exp_manager.experiment)
            states, msgs = exp_manager.get_simulation_status()
            exp_manager.print_status(states, msgs, verbose=False)
            logger.info("")
    else:
        logger.info("Hard deleting ALL experiments ran from the current directory.\n%s experiments total." % len(exp_managers))

    choice = raw_input("Are you sure you want to continue with the selected action (Y/n)? ")

    if choice != "Y":
        logger.info("No action taken.")
        return

    for exp_manager in exp_managers:
        logger.info("Deleting %s" % exp_manager.experiment)
        exp_manager.hard_delete()


def stdout(args, unknownArgs):
    logger.info('Getting stdout...')

    exp_manager = reload_experiment(args)
    states, msgs = exp_manager.get_simulation_status()

    if args.succeeded:
        args.simIds = [k for k in states if states.get(k) in ['Succeeded']][:1]
    elif args.failed:
        args.simIds = [k for k in states if states.get(k) in ['Failed']][:1]
    else:
        args.simIds = [states.keys()[0]]

    if not exp_manager.status_succeeded(states):
        logger.warning('WARNING: not all jobs have finished successfully yet...')

    exp_manager.add_analyzer(StdoutAnalyzer(args.simIds, args.error))

    if args.comps:
        override_HPC_settings(exp_manager.setup, use_comps_asset_svc='1')

    exp_manager.analyze_experiment()


def progress(args, unknownArgs):
    logger.info('Getting progress...')

    exp_manager = reload_experiment(args)
    states, msgs = exp_manager.get_simulation_status()

    exp_manager.add_analyzer(ProgressAnalyzer(args.simIds))

    if args.comps:
        override_HPC_settings(exp_manager.setup, use_comps_asset_svc='1')

    exp_manager.analyze_experiment()


def analyze(args, unknownArgs):
    # logger.info('Analyzing results...')
    AnalyzeHelper.analyze(args, unknownArgs, builtinAnalyzers)


def create_batch(args, unknownArgs):
    AnalyzeHelper.create_batch(args, unknownArgs)


def list_batch(args, unknownArgs):
    AnalyzeHelper.list_batch(args, unknownArgs)


def delete_batch(args, unknownArgs):
    AnalyzeHelper.delete_batch(args, unknownArgs)


def clear_batch(args, unknownArgs):
    if len(unknownArgs) > 1:
        print "/!\\ BATCH WARNING /!\\"
        print 'Too many batch names are provided: %s' % unknownArgs
        exit()

    if args.batchId and len(unknownArgs) > 0:
        print "/!\\ BATCH WARNING /!\\"
        print 'Both batchId and batchName are provided. This action cannot take both!\n'
        exit()

    AnalyzeHelper.clear_batch(args.batchId, True)


def analyze_list(args, unknownArgs):
    logger.error('\n' + '\n'.join(builtinAnalyzers.keys()))


def log(args, unknownArgs):
    # Check if complete
    if args.complete:
        records = [r.__dict__ for r in LoggingDataStore.get_all_records()]
        with open('dtk_tools_log.csv', 'wb') as output_file:
            dict_writer = csv.DictWriter(output_file,
                                         fieldnames=[r for r in records[0].keys()if not r[0] == '_'],
                                         extrasaction='ignore')
            dict_writer.writeheader()
            dict_writer.writerows(records)
        print "Complete log written to dtk_tools_log.csv."
        return

    # Create the level
    level = 0
    if args.level == "INFO":
        level = 20
    elif args.level == "ERROR":
        level = 30

    modules = args.module if args.module else LoggingDataStore.get_all_modules()

    print "Presenting the last %s entries for the modules %s and level %s" % (args.number, modules, args.level)
    records = LoggingDataStore.get_records(level,modules,args.number)

    records_str = "\n".join(map(str, records))
    print records_str

    if args.export:
        with open(args.export, 'w') as fp:
            fp.write(records_str)

        print "Log written to %s" % args.export


def sync(args, unknownArgs):
    """
    Sync COMPS db with local db
    """
    # Create a default HPC setup parser
    sp = SetupParser('HPC')
    endpoint = sp.get('server_endpoint')
    COMPS_login(endpoint)

    exp_to_save = list()
    exp_deleted = 0

    # Test the experiments present in the local DB to make sure they still exist in COMPS
    for exp in DataStore.get_experiments(None):
        if exp.location == "HPC":
            try:
                _ = get_experiment_by_id(exp.exp_id)
            except:
                # The experiment doesnt exist on COMPS anymore -> delete from local
                DataStore.delete_experiment(exp)
                exp_deleted += 1

    # Consider experiment id option
    exp_id = args.exp_id if args.exp_id else None
    exp_name = args.exp_name if args.exp_name else None
    user = args.user if args.user else sp.get('user')

    if exp_name:
        experiments = get_experiments_by_name(exp_name, user)
        for experiment_data in experiments:
            experiment = COMPS_experiment_to_local_db(exp_id=str(experiment_data.id),
                                                      endpoint=endpoint,
                                                      verbose=False,
                                                      save_new_experiment=True)
            if experiment:
                exp_to_save.append(experiment)

    elif exp_id:
        # Create a new experiment
        experiment = COMPS_experiment_to_local_db(exp_id=exp_id,
                                                  endpoint=endpoint,
                                                  verbose=True,
                                                  save_new_experiment=False)
        # The experiment needs to be saved
        if experiment:
            exp_to_save.append(experiment)
    else:
        # By default only get experiments created in the last month
        # day_limit = args.days if args.days else day_limit_default
        day_limit = 30
        today = datetime.date.today()
        limit_date = today - datetime.timedelta(days=int(day_limit))

        # For each of them, check if they are in the db
        for exp in get_experiments_per_user_and_date(user, limit_date):
            # Create a new experiment
            experiment = COMPS_experiment_to_local_db(exp_id=str(exp.id),
                                                      endpoint=endpoint,
                                                      save_new_experiment=False)

            # The experiment needs to be saved
            if experiment:
                exp_to_save.append(experiment)

    # Save the experiments if any
    if len(exp_to_save) > 0 and exp_deleted == 0:
        DataStore.batch_save_experiments(exp_to_save)
        logger.info("The following experiments have been added to the database:")
        logger.info("\n".join(["- "+str(exp) for exp in exp_to_save]))
        logger.info("%s experiments have been updated in the DB." % len(exp_to_save))
        logger.info("%s experiments have been deleted from the DB." % exp_deleted)
    else:
        print("The database was already up to date.")

    # Start overseer
    BaseExperimentManager.check_overseer()

def version(args, unknownArgs):
    logger.info(" ____    ______  __  __          ______                ___ ")
    logger.info("/\\  _`\\ /\\__  _\\/\\ \\/\\ \\        /\\__  _\\              /\\_ \\")
    logger.info("\\ \\ \\/\\ \\/_/\\ \\/\\ \\ \\/'/'       \\/_/\\ \\/   ___     ___\\//\\ \\     ____  ")
    logger.info(" \\ \\ \\ \\ \\ \\ \\ \\ \\ \\ , <    _______\\ \\ \\  / __`\\  / __`\\\\ \\ \\   /',__\\ ")
    logger.info("  \\ \\ \\_\\ \\ \\ \\ \\ \\ \\ \\\\`\\ /\\______\\\\ \\ \\/\\ \\L\\ \\/\\ \\L\\ \\\\_\\ \\_/\\__, `\\")
    logger.info("   \\ \\____/  \\ \\_\\ \\ \\_\\ \\_\\/______/ \\ \\_\\ \\____/\\ \\____//\\____\\/\\____/")
    logger.info("    \\/___/    \\/_/  \\/_/\\/_/          \\/_/\\/___/  \\/___/ \\/____/\\/___/")
    logger.info("Version: " + get_tools_revision())


# List experiments from local database
def db_list(args, unknownArgs):
    format_string = "%s - %s (%s) - %d simulations - %s"
    experiments = []

    # Filter by location
    if len(unknownArgs) > 0:
        if len(unknownArgs) == 1:
            experiments = DataStore.get_recent_experiment_by_filter(location=unknownArgs[0][2:].upper())
        else:
            raise Exception('Too many unknown arguments: please see help.')

    # Limit number of experiments to display
    elif args.limit:
        if args.limit.isdigit():
            experiments = DataStore.get_recent_experiment_by_filter(num=args.limit)

        elif args.limit == '*':
            experiments = DataStore.get_recent_experiment_by_filter(is_all=True)

        else:
            raise Exception('Invalid limit: please see help.')

    # Filter by experiment name like
    elif args.exp_name:
        experiments = DataStore.get_recent_experiment_by_filter(name=args.exp_name)

    # No args given
    else:
        experiments = DataStore.get_recent_experiment_by_filter()

    if len(experiments) > 0:
        for exp in experiments:
            print format_string % (exp.date_created.strftime('%m/%d/%Y %H:%M:%S'), exp.exp_id, exp.location,
                                   len(exp.simulations), "Completed" if exp.is_done() else "Not Completed")
    else:
        print "No experiments to display."


def analyze_from_script(args, sim_manager):
    # get simulation-analysis instructions from script
    mod = load_config_module(args.config_name)

    # analyze the simulations
    for analyzer in mod.analyzers:
        sim_manager.add_analyzer(analyzer)


def reload_experiment(args=None, try_sync=True):
    """
    Return the experiment (for given expId) or most recent experiment
    """
    exp_id = args.expId if args else None
    exp = DataStore.get_most_recent_experiment(exp_id)
    if not exp and try_sync and exp_id:
        try:
            exp = retrieve_experiment(exp_id,verbose=False)
        except:
            exp = None

    if not exp:
        logger.error("No experiment found with the ID '%s' Locally or in COMPS. Exiting..." % exp_id)
        exit()

    return ExperimentManagerFactory.from_experiment(exp)


def reload_experiments(args=None):
    id = args.expId if args else None
    current_dir = args.current_dir if 'current_dir' in args else None

    return map(lambda exp: ExperimentManagerFactory.from_experiment(exp), DataStore.get_experiments_with_options(id, current_dir))


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

    # 'dtk list' options
    parser_list = subparsers.add_parser('list',
                                        help='Report recent 20 list of simulations in experiment.')
    parser_list.add_argument(dest='exp_name', default=None, nargs='?', help='Experiment name.')
    parser_list.add_argument('-n', '--number',  help='Get given number recent experiment list', dest='limit')
    parser_list.set_defaults(func=db_list)

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
    parser_delete = subparsers.add_parser('delete', help='Delete most recent experiment (tracking objects only, e.g., local cache) specified by ID or name.')
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
    parser_analyze = subparsers.add_parser('analyze', help='Analyze finished simulations in experiment according to analyzers.')
    parser_analyze.add_argument('-bn', '--batchName', dest='batchName', default=None, nargs='?', help='Use Batch Name for analyze.')
    parser_analyze.add_argument('-i', '--ids', dest='itemids', default=None, nargs='*', help='IDs of the items to analyze (can be suites, batches, experiments)')
    parser_analyze.add_argument('-a', '--config_name', dest='config_name', default=None,  help='Python script or builtin analyzer name for custom analysis of simulations.')
    parser_analyze.add_argument('-f', '--force', action='store_true', help='Force analyzer to run even if jobs are not all finished.')
    parser_analyze.set_defaults(func=analyze)

    # 'dtk create_batch' options
    parser_analyze = subparsers.add_parser('create_batch',     help='Create a Batch for later use in Analyze.')
    parser_analyze.add_argument('-bn', '--batchName', dest='batchName', default=None, nargs='?', help='Use Batch Name.')
    parser_analyze.add_argument('-i', '--ids', dest='itemids', default=None, nargs='*', help='IDs of the items to analyze (can be suites, batches, experiments)')
    parser_analyze.set_defaults(func=create_batch)

    # 'dtk list_batch' options
    parser_list = subparsers.add_parser('list_batch', help='Report recent 20 list of batches in Batch.')
    parser_list.add_argument('-bid', dest='batchId', default=None, nargs='?', help='Batch ID.')
    parser_list.add_argument('-n', '--number',  dest='limit', help='Get given number recent batch list')
    parser_list.set_defaults(func=list_batch)

    # 'dtk delete_batch' options
    parser_clean = subparsers.add_parser('delete_batch', help='Delete all Batches or Batch with given Batch ID.')
    parser_clean.add_argument('-bid', dest='batchId', default=None, nargs='?', help='Batch ID.')
    parser_clean.set_defaults(func=delete_batch)

    # 'dtk clear_batch' options
    parser_clean = subparsers.add_parser('clear_batch', help='Remove all associated experiments from Batch or remove all Batches with empty experiments.')
    parser_clean.add_argument('-bid', dest='batchId', default=None, nargs='?', help='Batch ID.')
    parser_clean.set_defaults(func=clear_batch)

    # 'dtk analyze-list' options
    parser_analyze_list = subparsers.add_parser('analyze-list', help='List the available builtin analyzers.')
    parser_analyze_list.set_defaults(func=analyze_list)

    # 'dtk sync' options
    parser_sync = subparsers.add_parser('sync', help='Synchronize the COMPS database with the local database.')
    parser_sync.add_argument('-d', '--days',  help='Limit the sync to a certain number of days back', dest='days')
    parser_sync.add_argument('-id', '--exp_id', help='Sync a specific experiment from COMPS.', dest='exp_id')
    parser_sync.add_argument('-n', '--name', help='Sync a specific experiment from COMPS (use %% for wildcard character).', dest='exp_name')
    parser_sync.add_argument('-u', '--user', help='Sync experiments belonging to a particular user', dest='user')
    parser_sync.set_defaults(func=sync)

    # 'dtk version' options
    parser_version = subparsers.add_parser('version', help='Display the current dtk-tools version.')
    parser_version.set_defaults(func=version)

    # 'dtk setup' options
    # parser_setup = subparsers.add_parser('setup', help='Launch the setup UI allowing to edit ini configuration files.')
    # parser_setup.set_defaults(func=setup)

    # Testing: 'dtk setup' options
    parser_setup = subparsers.add_parser('setup2', help='Launch the setup UI allowing to edit ini configuration files.')
    parser_setup.set_defaults(func=setup2)

    # 'dtk test' options
    parser_test = subparsers.add_parser('test', help='Launch the nosetests on the test folder.')
    parser_test.set_defaults(func=test)

    # 'dtk log' options
    parser_log = subparsers.add_parser('log', help="Allow to query and export the logs.")
    parser_log.add_argument('-l', '--level', help="Only display logs for a certain level and above (DEBUG,INFO,ERROR)", dest="level", default="DEBUG")
    parser_log.add_argument('-m', '--module', help="Only display logs for a given module.", dest="module", nargs='+')
    parser_log.add_argument('-n', '--number', help="Limit the number of entries returned (default is 100).", dest="number", default=100)
    parser_log.add_argument('-e', '--export', help="Export the log to the given file.", dest="export")
    parser_log.add_argument('-c', '--complete', help="Export the complete log to a CSV file (dtk_tools_log.csv).", action='store_true')
    parser_log.set_defaults(func=log)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()
    args.func(args, unknownArgs)


if __name__ == '__main__':
    main()
