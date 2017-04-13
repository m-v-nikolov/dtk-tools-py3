import json
import os
import sys
from importlib import import_module

from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore
from simtools.DataAccess.Schema import Batch, Experiment
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.Utilities.General import init_logging, retrieve_item

logger = init_logging('Commands')


def analyze(args, unknownArgs, builtinAnalyzers):
    # logger.info('Analyzing results...')

    # validate parameters
    validate_parameters(args, unknownArgs)

    # collect all experiments
    exp_dict = collect_experiments(args)

    # case: args.batchName is provided
    if args.batch_name:
        batch = DataStore.get_batch_by_name(args.batch_name)
        if batch:
            exp_id_list_from_batch = batch.get_experiment_ids()
            exp_id_list = exp_dict.keys()

            if not compare_two_ids_list(exp_id_list, exp_id_list_from_batch):

                # confirm only if existing batch contains different experiments
                logger.info(
                    "\nBatch with name %s already exists and contains the following experiment(s):\n" % args.batch_name)
                logger.info('\n'.join([' - %s' % exp_id for exp_id in exp_id_list_from_batch]))

                if exp_dict:
                    var = raw_input('\nDo you want to [O]verwrite, [M]erge, or [C]ancel:  ')
                    # print "You selected '%s'" % var
                    if var == 'O':
                        # clear existing experiments associated with this Batch
                        DataStore.clear_batch(batch)
                    elif var == 'M':
                        # collect 'new' experiments to be added to the existing batch
                        for exp_id in exp_id_list_from_batch:
                            if not exp_dict.has_key(exp_id):
                                exp_dict[exp_id] = retrieve_experiment(exp_id)
                    elif var == 'C':
                        exit()
                    else:
                        logger.error("Option '%s' is invalid..." % var)
                        exit()
            else:
                pass

    # check status for each experiment
    if not args.force:
        check_status(exp_dict.values())

    # collect all analyzers
    analyzers = collect_analyzers(args, builtinAnalyzers)

    if not exp_dict:
        # No experiment specified -> using latest
        latest = DataStore.get_most_recent_experiment()
        exp_dict[latest.exp_id] = latest

    # create instance of AnalyzeManager
    analyzeManager = AnalyzeManager(exp_dict.values(), analyzers)

    # if batch name exists, always save experiments
    if args.batch_name:
        # save/create batch
        save_batch(args, exp_dict.values())
    # Only create a batch if we pass more than one experiment
    elif len(exp_dict) != 1:
        # check if there is any existing batch containing the same experiments
        batch_existing = check_existing_batch(exp_dict)

        if batch_existing is None or args.batch_name:
            # save/create batch
            save_batch(args, exp_dict.values())
        else:
            # display the existing batch
            logger.info('\nBatch: %s (id=%s)' % (batch_existing.name, batch_existing.id))

    # start to analyze
    analyzeManager.analyze()

    # remove empty batches
    clean_batch()


def validate_parameters(args, unknownArgs):
    if args.config_name is None:
        logger.info('Please provide Analyzer (-a or --config_name).')
        exit()


def check_existing_batch(exp_list):
    exp_list_ids = exp_list.keys()
    batch_list = DataStore.get_batch_list()

    for batch in batch_list:
        batch_list_ids = batch.get_experiment_ids()

        if compare_two_ids_list(exp_list_ids, batch_list_ids):
            return batch

    return None


def compare_two_ids_list(ids_1, ids_2):
    return len(ids_1) == len(ids_2) and set(ids_1) == set(ids_2)


def save_batch(args, final_exp_list=None):
    if len(final_exp_list) == 0:
        logger.info('Please provide some experiment(s) to analyze.')
        exit()

    batch = DataStore.get_batch_by_name(args.batch_name)
    existing = True if batch else False

    # create a new Batch if not exists
    if batch is None:
        batch = Batch()

    # add experiments
    for exp in final_exp_list:
        # ok, SqlAlchemy won't add duplicated experiment
        batch.experiments.append(exp)

    # create batch and save with experiments
    batch_id = DataStore.save_batch(batch)

    # update batch name with new id if no name is provided
    batch_name = 'batch_%s' % batch_id if not args.batch_name else args.batch_name
    if not args.batch_name or not existing:
        new_batch = DataStore.get_batch_by_id(batch_id)
        new_batch.name = batch_name
        DataStore.save_batch(new_batch)

    logger.info('\nBatch: %s (id=%s)' % (batch_name, batch_id))

    return batch_id


def create_batch(args, unknownArgs):
    """
     - create or use existing batch
    """
    # collect all experiments
    exps = collect_experiments(args)

    # save/create batch
    save_batch(args, exps.values())


def collect_analyzers(args, builtinAnalyzers):
    analyzers = []

    if os.path.exists(args.config_name):
        # get analyzers from script
        mod = load_config_module(args.config_name)

        # analyze the simulations
        for analyzer in mod.analyzers:
            analyzers.append(analyzer)
    elif args.config_name in builtinAnalyzers.keys():
        # get provided analyzer
        analyzers.append(builtinAnalyzers[args.config_name])
    else:
        logger.error('Unknown analyzer...available builtin analyzers: ' + ', '.join(builtinAnalyzers.keys()))
        exit()

    return analyzers


def collect_experiments(args):
    experiments = dict()

    # retrieve ids
    ids = args.itemids

    if not ids: return experiments

    # For each, treat it differently depending on what it is
    for itemid in ids:
        item = retrieve_item(itemid)
        # We got back a list of experiment
        if isinstance(item, list):
            experiments.update({i.exp_id: i for i in item})
        elif isinstance(item, Experiment):
            experiments[item.exp_id] = item
        elif isinstance(item, Batch):
            # We have to retrieve_experiment even if we already have the experiment object
            # to make sure we are loading the simulations associated with it
            experiments.update({i.exp_id: retrieve_experiment(i.exp_id) for i in item.experiments})

    return experiments


def check_status(exp_list):
    for exp in exp_list:
        exp_manager = ExperimentManagerFactory.from_experiment(exp)
        exp_manager.analyzers = []
        states, msgs = exp_manager.get_simulation_status()
        if not exp_manager.status_succeeded(states):
            logger.warning('Not all jobs have finished successfully yet...')
            logger.info('Job states:')
            logger.info(json.dumps(states, sort_keys=True, indent=4))
            exit()


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
    else:
        logger.error("Unexpected error: %s", sys.exc_info()[0])
        raise


def list_batch(args, unknownArgs):
    """
    List experiments from local database
    """
    if len(unknownArgs) > 1:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('Too many batch names are provided: %s' % unknownArgs)
        exit()

    batches = None
    if args.batch_id and len(unknownArgs) > 0:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('Both batchId and batchName are provided. We will ignore both and list all batches in DB!\n')
        batches = DataStore.get_batch_list()
    elif args.batch_id:
        batches = DataStore.get_batch_list(args.batch_id)
    elif len(unknownArgs) > 0:
        batches = DataStore.get_batch_list_by_name(unknownArgs[0])
    else:
        batches = DataStore.get_batch_list()

    display_batch(batches)


def display_batch(batches):
    if batches:
        logger.info('---------- Batch(s) in DB -----------')
        if isinstance(batches, list):
            for batch in batches:
                logger.info('%s (id=%s, count=%s)' % (batch.name, batch.id, len(batch.experiments)))
                for exp in batch.experiments:
                    logger.info(' - %s' % exp.exp_id)
            logger.info('\nTotal: %s Batch(s)' % len(batches))
        else:
            logger.info('%s (id=%s, count=%s)' % (batches.name, batches.id, len(batches.experiments)))
            for exp in batches.experiments:
                logger.info(' - %s' % exp.exp_id)
            logger.info('\nTotal: 1 Batch')
    else:
        logger.info('There is no Batch records in DB.')


def delete_batch(args, unknownArgs):
    """
    Delete a particular batch or all batches in DB
    """
    if len(unknownArgs) > 1:
        logger.error('Too many parameters are provided: %s' % unknownArgs)
        exit()

    if args.batch_id and len(unknownArgs) > 0:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('Both batchId and batchName are provided. This action cannot take both!\n')
        exit()

    msg = ''
    if args.batch_id:
        msg = 'Are you sure you want to delete the Batch %s (Y/n)? ' % args.batch_id
    else:
        msg = 'Are you sure you want to delete all Batches (Y/n)? '

    choice = raw_input(msg)

    if choice != 'Y':
        logger.warning('No action taken.')
        return
    else:
        DataStore.delete_batch(args.batch_id)
        logger.info('The Batch(s) have been deleted.')


def clear_batch(batch_id_or_name, ask=False):
    """
    - de-attach all associated experiments from the given batch
      or
    - remove all empty batches
    """

    if batch_id_or_name is None:
        logger.info("Please provide a batch is or name.")
        exit()

    batch = DataStore.get_batch_by_id(batch_id_or_name)

    if batch is None:
        batch = DataStore.get_batch_by_name(batch_id_or_name)

    if batch is None:
        logger.info("The Batch given by '%s' doesn't exist! ." % batch_id_or_name)
        exit()

    if ask:
        msg = 'Are you sure you want to detach all associated experiments (Y/n)? '
        choice = raw_input(msg)

        if choice != 'Y':
            logger.warning('No action taken.')
            return
        else:
            DataStore.clear_batch(batch)
            logger.info('The associated experiments have been detached.')


def clean_batch(ask=False):
    """
    - remove all empty batches
    """
    if ask:
        msg = 'Are you sure you want to remove all empty Batches (Y/n)? '
        choice = raw_input(msg)

        if choice != 'Y':
            logger.warning('No action taken.')
            return

    cnt = DataStore.remove_empty_batch()
    if cnt > 0:
        logger.info('The Total %s empty Batch(s) have been removed.' % cnt)
