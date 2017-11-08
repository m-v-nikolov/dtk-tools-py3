import argparse
import csv
import datetime
import os
import shutil
import subprocess

import simtools.AnalyzeManager.AnalyzeHelper as AnalyzeHelper
from dtk import commands_args
from dtk.utils.analyzers import StdoutAnalyzer
from dtk.utils.analyzers import TimeseriesAnalyzer, VectorSpeciesAnalyzer
from dtk.utils.analyzers import sample_selection
from dtk.utils.analyzers.group import group_by_name
from dtk.utils.analyzers.plot import plot_grouped_lines
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore
from simtools.DataAccess.LoggingDataStore import LoggingDataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import get_experiments_per_user_and_date, get_experiments_by_name, COMPS_login, \
    get_experiment_ids_for_user
from simtools.Utilities.Experiments import COMPS_experiment_to_local_db, retrieve_experiment
from simtools.Utilities.General import nostdout, get_tools_revision, retrieve_item
from COMPS.Data.Simulation import SimulationState
from simtools.Utilities.GitHub.GitHub import GitHub, DTKGitHub
import simtools.Utilities.Initialization as init
from simtools.DataAccess.Schema import Experiment, Simulation

from simtools.Utilities.General import init_logging
logger = init_logging('Commands')


def builtinAnalyzers():
    analyzers = {
        'time_series': TimeseriesAnalyzer(select_function=sample_selection(), group_function=group_by_name('_site_'),
                                          plot_function=plot_grouped_lines),
        'vector_species': VectorSpeciesAnalyzer(select_function=sample_selection(), group_function=group_by_name('_site_')),
    }

    return analyzers


class objectview(object):
    def __init__(self, d):
        self.__dict__ = d


def test(args, unknownArgs):
    # Get to the test dir
    current_dir = os.path.dirname(os.path.realpath(__file__))
    test_dir = os.path.abspath(os.path.join(current_dir, '..', 'test'))

    # Create the test command
    command = ['nosetests']
    command.extend(unknownArgs)

    # Run
    subprocess.Popen(command, cwd=test_dir).wait()


def run(args, unknownArgs):
    # get simulation-running instructions from script
    mod = args.loaded_module

    # Make sure we have run_sim_args
    if not hasattr(mod, 'run_sim_args'):
        if hasattr(mod, 'run_calib_args'):
            print("The module you are trying to run seems to contain a calibration script and should be ran with the "
                  "`calibtool run` command.")
            exit()

        import json
        print("You are trying to run a module without the required run_sim_args dictionary.")
        print("The run_sim_args is expected to be of the format:")
        print(json.dumps({"config_builder": "cb",
                          "exp_name": "Experiment_name",
                          "exp_builder": "Optional builder"}, indent=3))
        exit()

    # Assess arguments.
    mod.run_sim_args['blocking'] = True if args.blocking else False
    mod.run_sim_args['quiet']    = True if args.quiet    else False

    # Create the experiment manager
    exp_manager = ExperimentManagerFactory.init()
    exp_manager.run_simulations(**mod.run_sim_args)


def status(args, unknownArgs):
    # No matter what check the overseer
    from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
    BaseExperimentManager.check_overseer()

    if args.active:
        print('Getting status of all active dtk experiments.')
        active_experiments = DataStore.get_active_experiments()

        for exp in active_experiments:
            exp_manager = ExperimentManagerFactory.from_experiment(exp)
            exp_manager.print_status()
        return
    exp_manager = reload_experiment(args)
    if args.repeat:
        exp_manager.wait_for_finished(verbose=True, sleep_time=20)
    else:
        exp_manager.print_status()


def kill(args, unknownArgs):
    with nostdout():
        exp_manager = reload_experiment(args)

    logger.info("Killing Experiment %s" % exp_manager.experiment.id)
    states, msgs = exp_manager.get_simulation_status()
    exp_manager.print_status(states, msgs, verbose=False)

    if exp_manager.status_finished(states):
        logger.warn("The Experiment %s is already finished and therefore cannot be killed. Exiting..." % exp_manager.experiment.id)
        return

    if args.simIds:
        logger.info('Killing job(s) with ids: ' + str(args.simIds))
    else:
        logger.info('No job IDs were specified.  Killing all jobs in selected experiment (or most recent).')

    choice = input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logger.info('No action taken.')
        return

    exp_manager.kill(args.simIds)
    logger.info("'Kill' has been executed successfully.")


def exterminate(args, unknownArgs):
    exp_managers = reload_experiments(args)

    if args.expId:
        for exp_manager in exp_managers:
            states, msgs = exp_manager.get_simulation_status()
            exp_manager.print_status(states, msgs)
        ('Killing ALL experiments matched by ""' + args.expId + '".')
    else:
        logger.info('Killing ALL running experiments.')

    logger.info('%s experiments found.' % len(exp_managers))
    for manager in exp_managers:
        print(manager.experiment)

    choice = input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logger.info('No action taken.')
        return

    for manager in exp_managers:
        manager.cancel_experiment()

    print("'Exterminate' has been executed successfully.")


def link(args, unknownArgs):
    """
    Open browser to the COMPS Experiment/Simulation with ID or name provided
    :param args:
    :param unknownArgs:
    :return:
    """

    # get input from commands line
    input_id = args.Id

    # default: consider the latest experiment
    if input_id is None:
        latest = DataStore.get_most_recent_experiment()
        input_id = latest.exp_id

    try:
        comps_item = retrieve_item(input_id)
    except:
        print('Nothing was found for {}'.format(input_id))
        exit()

    # check item type
    id_type = ''
    location = 'LOCAL'
    if isinstance(comps_item, Experiment):
        item_id = comps_item.exp_id
        id_type = 'exp'
        location = comps_item.location
    elif isinstance(comps_item, Simulation):
        item_id = comps_item.id
        exp_id = comps_item.experiment_id
        id_type = 'sim'
        # retrieve location
        exp = DataStore.get_experiment(exp_id)
        location = exp.location
    else:
        print('No Experiment or Simulation was found on COMPS for {}'.format(input_id))
        exit()

    # make sure it exists on COMPS
    if location == 'LOCAL':
        print('Item is on LOCAL not on COMPS.')
        exit()

    # open browser to COMPS Experiment/Simulation
    import webbrowser
    with SetupParser.TemporarySetup(temporary_block='HPC') as sp:
        endpoint = sp.get('server_endpoint')

    url = ''
    if id_type == 'exp':
        url = '%s/#explore/Experiments?filters=Id=%s&offset=0&selectedId=%s' % (endpoint, item_id, item_id)
    elif id_type == 'sim':
        url = '%s/#explore/Simulations?filters=Id=%s&mode=list&orderby=DateCreated+desc&count=50&offset=0&layout=512C56&selectedId=%s' % (endpoint, item_id, item_id)

    # Open URL in new browser window
    webbrowser.open_new(url)  # opens in default browser


def delete(args, unknownArgs):
    exp_manager = reload_experiment(args)
    if exp_manager is None:
        logger.info("The experiment doesn't exist. No action executed.")
        return

    states, msgs = exp_manager.get_simulation_status()
    exp_manager.print_status(states, msgs)

    print("The following experiment will be deleted:")
    print(exp_manager.experiment)

    choice = input('Are you sure you want to continue with the selected action (Y/n)? ')

    if choice != 'Y':
        logger.info('No action taken.')
        return

    exp_manager.delete_experiment()
    logger.info("Experiment '%s' has been successfully deleted.", exp_manager.experiment.exp_id)


def clean(args, unknownArgs):

    # Store the current directory to let the reload knows that we want to
    # only retrieve simulations in this directory
    args.current_dir = os.getcwd()
    exp_managers = reload_experiments(args)

    if len(exp_managers) == 0:
        logger.warn("No experiments matched. Exiting...")
        return

    if args.expId:
        logger.info("Hard deleting ALL experiments matched by '%s' ran from the current directory.\n%s experiments total." % (args.expId, len(exp_managers)))
        for exp_manager in exp_managers:
            logger.info(exp_manager.experiment)
    else:
        logger.info("Hard deleting ALL experiments ran from the current directory.\n%s experiments total." % len(exp_managers))

    for exp_manager in exp_managers:
        print(exp_manager.experiment)

    choice = input("Are you sure you want to continue with the selected action (Y/n)? ")

    if choice != "Y":
        logger.info("No action taken.")
        return

    for exp_manager in exp_managers:
        logger.info("Deleting %s" % exp_manager.experiment)
        exp_manager.delete_experiment()


def stdout(args, unknownArgs):
    exp_manager = reload_experiment(args)
    states, msgs = exp_manager.get_simulation_status()

    if not exp_manager.status_succeeded(states):
        logger.warning('WARNING: not all jobs have finished successfully yet...')

    found = False
    for sim_id, state in states.items():
        if (state is SimulationState.Succeeded and args.succeeded) or\
               (state is SimulationState.Failed and args.failed) or \
               (not args.succeeded and not args.failed):
            found = True
            break
    if not found:
        print("No simulations found...")
    else:
        am = AnalyzeManager(exp_list=[exp_manager.experiment],
                            analyzers=StdoutAnalyzer([sim_id], args.error),
                            force_analyze=True)
        am.analyze()


def analyze(args, unknownArgs):
    # logger.info('Analyzing results...')
    args.config_name = args.analyzer # prevents need for underlying refactor
    AnalyzeHelper.analyze(args, unknownArgs, builtinAnalyzers())


def create_batch(args, unknownArgs):
    AnalyzeHelper.create_batch(args.batch_name, args.itemids)


def list_batch(args, unknownArgs):
    id_or_name = None
    if args.id_or_name and len(unknownArgs) > 0:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('More than one Batch Id/Name are provided. We will ignore both and list all batches in DB!\n')
    else:
        id_or_name = args.id_or_name

    AnalyzeHelper.list_batch(id_or_name=id_or_name)


def delete_batch(args, unknownArgs):
    if args.batch_id and len(unknownArgs) > 0:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('More than one Batch Id/Name are provided. Exiting...\n')
        exit()
    AnalyzeHelper.delete_batch(args.batch_id)


def clean_batch(args, unknownArgs):
    AnalyzeHelper.clean_batch(ask=True)


def clear_batch(args, unknownArgs):
    AnalyzeHelper.clear_batch(id_or_name=args.id_or_name,ask=True)


def analyze_list(args, unknownArgs):
    print('\n' + '\n'.join(sorted(builtinAnalyzers().keys())))


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
        print("Complete log written to dtk_tools_log.csv.")
        return

    # Create the level
    level = 0
    if args.level == "INFO":
        level = 20
    elif args.level == "ERROR":
        level = 30

    modules = args.module if args.module else LoggingDataStore.get_all_modules()

    print("Presenting the last %s entries for the modules %s and level %s" % (args.number, modules, args.level))
    records = LoggingDataStore.get_records(level,modules,args.number)

    records_str = "\n".join(map(str, records))
    print(records_str)

    if args.export:
        with open(args.export, 'w') as fp:
            fp.write(records_str)

        print("Log written to %s" % args.export)


def sync(args, unknownArgs):
    """
    Sync COMPS db with local db
    """
    # Create a default HPC setup parser
    with SetupParser.TemporarySetup(temporary_block='HPC') as sp:
        endpoint = sp.get('server_endpoint')
        user = sp.get('user')
        COMPS_login(endpoint)

    exp_to_save = list()
    exp_deleted = 0

    # Retrieve all the experiment id from COMPS for the current user
    exp_ids = get_experiment_ids_for_user(user)

    # Test the experiments present in the local DB to make sure they still exist in COMPS
    for exp in DataStore.get_experiments():
        if exp.location == "HPC":
            if exp.exp_id not in exp_ids:
                # The experiment doesnt exist on COMPS anymore -> delete from local
                DataStore.delete_experiment(exp)
                exp_deleted += 1

    # Consider experiment id option
    exp_id = args.exp_id if args.exp_id else None
    exp_name = args.exp_name if args.exp_name else None
    user = args.user if args.user else user

    if exp_name:
        experiments = get_experiments_by_name(exp_name, user)
        for experiment_data in experiments:
            experiment = COMPS_experiment_to_local_db(exp_id=str(experiment_data.id),
                                                      endpoint=endpoint,
                                                      verbose=True,
                                                      save_new_experiment=False)
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
    # Filter by location
    selected_block = None
    num = 20
    is_all = False
    name = None

    if len(unknownArgs) > 0:
        if len(unknownArgs) == 1:
            selected_block = unknownArgs[0][2:].upper()
        else:
            raise Exception('Too many unknown arguments: please see help.')

    # Limit number of experiments to display
    if args.limit:
        if args.limit.isdigit():
            num = args.limit
        elif args.limit == '*':
            is_all=True
        else:
            raise Exception('Invalid limit: please see help.')

    # Filter by experiment name like
    if args.exp_name: name=args.exp_name

    # Execute query
    experiments = DataStore.get_recent_experiment_by_filter(num=num, name=name, is_all=is_all, location=selected_block)

    if len(experiments) > 0:
        for exp in experiments:
            print(exp)
    else:
        print("No experiments to display.")


def list_packages(args, unknownArgs):
    print("The following packages are available to install:")
    package_names = DTKGitHub.get_package_list()
    package_names.remove(DTKGitHub.TEST_DISEASE_PACKAGE_NAME) # don't show the test package/repo!
    for package in package_names:
        print(" - {}".format(package))

    print("\nYou can install them with the following command:\n"
          "`dtk get_package <PACKAGE_NAME>`")
    return package_names


def list_package_versions(args, unknownArgs):
    try:
        package_name = args.package_name
        github = DTKGitHub(disease=package_name)
        print("The following versions are available for the package {}".format(package_name))
        versions = github.get_versions()
        for v in versions:
            print(" - {}".format(v))
        print("\nYou can install a specific version with the following command:\n"
              "`dtk get_package <PACKAGE_NAME> -v <VERSION>`")
    except GitHub.AuthorizationError:
        versions = []
    return versions


def get_package(args, unknownArgs):
    import pip
    import tempfile
    import zipfile
    is_test = args.is_test if hasattr(args, 'is_test') else None # test == no pip install

    # overwrite any existing package by the same name (any version) with the specified version
    release_dir = None
    try:
        package_name = args.package_name
        github = DTKGitHub(disease=package_name)

        if args.package_version.upper() == GitHub.HEAD:
            version = GitHub.HEAD
        elif args.package_version.lower() == 'latest':
            version = github.get_latest_version() # if no versions exist, returns None
        elif github.version_exists(version=args.package_version):
            version = args.package_version
        else:
            version = None

        if version is None:
            print("Requested version: %s for package: %s does not exist. No changes made." % (args.package_version, package_name))
            return

        tempdir = tempfile.mkdtemp()
        zip_filename = github.get_zip(version=version, destination=tempdir)

        # Unzip the obtained zip
        zip_ref = zipfile.ZipFile(zip_filename, 'r')
        zip_ref.extractall(tempdir)
        zip_ref.close()
        os.remove(zip_filename)

        # Identify the unziped source directory
        source_dir_candidates = [f for f in os.listdir(tempdir) if
                                 'InstituteforDiseaseModeling-%s' % DTKGitHub.PACKAGE_LIST[package_name] in f]
        if len(source_dir_candidates) != 1:
            raise Exception('Failure to identify package to install')
        else:
            source_dir = source_dir_candidates[0]
        release_dir = os.path.join(os.path.dirname(zip_filename), source_dir)

        # edit source dir setup file for the correct version
        setup_file = os.path.join(release_dir, 'setup.py')
        with open(setup_file, 'r') as file:
            text = file.read()
        text = text.replace('$VERSION$', str(version))
        with open(setup_file, 'w') as file:
            file.write(text)

        # install
        if not is_test:
            pip.main(['install', '--no-dependencies', '--ignore-installed', release_dir])

        # update the local DB with the version
        db_key = github.disease_package_db_key
        DataStore.save_setting(DataStore.create_setting(key=db_key, value=str(version)))
        shutil.rmtree(tempdir)
    except GitHub.AuthorizationError:
        pass

    return release_dir


def analyze_from_script(args, sim_manager):
    # get simulation-analysis instructions from script
    mod = init.load_config_module(args.config_name)

    # analyze the simulations
    for analyzer in mod.analyzers:
        sim_manager.add_analyzer(analyzer)


def reload_experiment(args=None, try_sync=True):
    """
    Return the experiment (for given expId) or most recent experiment
    """
    exp_id = args.expId if args else None
    if not exp_id:
        exp = DataStore.get_most_recent_experiment(exp_id)
    elif try_sync:
        try:
            exp = retrieve_experiment(exp_id,verbose=False)
        except:
            exp = None

    if not exp:
        logger.error("No experiment found with the ID '%s' Locally or in COMPS. Exiting..." % exp_id)
        exit()

    return ExperimentManagerFactory.from_experiment(exp)


def reload_experiments(args=None):
    exp_id = args.expId if hasattr(args, 'expId') else None
    current_dir = args.current_dir if hasattr(args, 'current_dir') else None

    managers = []
    experiments = DataStore.get_experiments_with_options(exp_id, current_dir)
    for exp in experiments:
        try:
            managers.append(ExperimentManagerFactory.from_experiment(exp))
        except RuntimeError:
            print("Could not create manager... Bypassing...")
    return managers


def main():
    parser = argparse.ArgumentParser(prog='dtk')
    subparsers = parser.add_subparsers()

    # 'dtk run' options
    commands_args.populate_run_arguments(subparsers, run)

    # 'dtk status' options
    commands_args.populate_status_arguments(subparsers, status)

    # 'dtk list' options
    commands_args.populate_list_arguments(subparsers, db_list)

    # 'dtk kill' options
    commands_args.populate_kill_arguments(subparsers, kill)

    # 'dtk exterminate' options
    commands_args.populate_exterminate_arguments(subparsers, exterminate)

    # 'dtk link' options
    commands_args.populate_link_arguments(subparsers, link)

    # 'dtk delete' options
    commands_args.populate_delete_arguments(subparsers, delete)

    # 'dtk clean' options
    commands_args.populate_clean_arguments(subparsers, clean)

    # 'dtk stdout' options
    commands_args.populate_stdout_arguments(subparsers, stdout)

    # 'dtk analyze' options
    commands_args.populate_analyze_arguments(subparsers, analyze)

    # 'dtk create_batch' options
    commands_args.populate_createbatch_arguments(subparsers, create_batch)

    # 'dtk list_batch' options
    commands_args.populate_listbatch_arguments(subparsers, list_batch)

    # 'dtk delete_batch' options
    commands_args.populate_deletebatch_arguments(subparsers, delete_batch)

    # 'dtk clear_batch' options
    commands_args.populate_clearbatch_arguments(subparsers, clear_batch)

    # 'dtk clean_batch' options
    commands_args.populate_cleanbatch_arguments(subparsers, clean_batch)

    # 'dtk analyze-list' options
    commands_args.populate_analyzer_list_arguments(subparsers, analyze_list)

    # 'dtk sync' options
    commands_args.populate_sync_arguments(subparsers, sync)

    # 'dtk version' options
    commands_args.populate_version_arguments(subparsers, version)

    # 'dtk test' options
    commands_args.populate_test_arguments(subparsers, test)

    # 'dtk log' options
    commands_args.populate_log_arguments(subparsers, log)

    # 'dtk list_packages' options
    commands_args.populate_list_packages_arguments(subparsers, list_packages)

    # 'dtk list_package_versions' options
    commands_args.populate_list_package_versions_arguments(subparsers, list_package_versions)

    # 'dtk get_package' options
    commands_args.populate_get_package_arguments(subparsers, get_package)

    # run specified function passing in function-specific arguments
    args, unknownArgs = parser.parse_known_args()

    # This is it! This is where SetupParser gets set once and for all. Until you run 'dtk COMMAND' again, that is.
    init.initialize_SetupParser_from_args(args, unknownArgs)

    try:
        args.func(args, unknownArgs)
    except AttributeError:
        parser.print_help()

if __name__ == '__main__':
    main()
