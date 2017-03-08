import json
import os
import sys
from importlib import import_module
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.BatchDataStore import Batch, BatchDataStore
from simtools.DataAccess.DataStore import DataStore
from simtools.DataAccess.ExperimentDataStore import ExperimentDataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.Utilities.General import init_logging

logger = init_logging('Analyze')


def analyze(args, unknownArgs, builtinAnalyzers):
    # logger.info('Analyzing results...')

    # validate parameters
    validate_parameters(args, unknownArgs)

    # collect all experiment ids
    exp_ids = collect_experiment_ids(args)

    # validate experiments (may sync from COMPS server)
    exp_list = reload_experiments(exp_ids)

    # check status for each experiment
    if not args.force:
        check_status(exp_list)

    # collect all analyzers
    analyzers = collect_analyzers(args, builtinAnalyzers)

    # consider user's choice: merge experiments with existing batch
    batch = BatchDataStore.get_batch_by_name(args.batchName)
    if batch:
        # reload experiment since exp from Batch.experiments doesn't have simulations pre-loaded!
        exp_existing = [ExperimentDataStore.get_experiment(exp.exp_id) for exp in batch.experiments]

    final_exp_list = exp_list + exp_existing if batch else exp_list

    # create instance of AnalyzeManager
    analyzeManager = AnalyzeManager(final_exp_list, analyzers)

    # save/create batch
    save_batch(args, final_exp_list)

    # start to analyze
    analyzeManager.analyze()

    # remove empty batches if there is any
    clear_batch()


def validate_parameters(args, unknownArgs):
    if args.config_name is None:
        print 'Please provide Analyze (-a or --config_name).'
        exit()


def save_batch(args, final_exp_list=None):
    if len(final_exp_list) == 0:
        print 'Please to provide some experiment(s) to analyze.'
        exit()

    batch = BatchDataStore.get_batch_by_name(args.batchName)
    existing = True if batch else False

    # create a new Batch if not exists
    if batch is None:
        batch = Batch()

    # add experiments
    for exp in final_exp_list:
        # ok, SqlAlchemy won't add duplicated experiment
        batch.experiments.append(exp)

    # create batch and save with experiments
    batch_id = BatchDataStore.save_batch(batch)

    # update batch name with new id if no name is provided
    batch_name = 'batch_%s' % batch_id if not args.batchName else args.batchName
    if not args.batchName or not existing:
        new_batch = BatchDataStore.get_batch_by_id(batch_id)
        new_batch.name = batch_name
        BatchDataStore.save_batch(new_batch)

    print '\nBatch: %s (id=%s)' % (batch_name, batch_id)

    return batch_id


def create_batch(args, unknownArgs):
    """
     - create or use existing batch
    """
    # collect all experiment ids
    exp_ids = collect_experiment_ids(args)

    # validate experiments (may sync from COMPS server)
    exp_list = reload_experiments(exp_ids)

    # save/create batch
    save_batch(args, exp_list)


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


def collect_experiment_ids(args):
    # retrieve parameters
    exp_ids = args.expId if args.expId else []
    batch_ids = args.batchId if args.batchId else []

    # retrieve experiments from batch_ids
    exp_ids_from_batch_ids = BatchDataStore.get_expIds_by_batchIds(batch_ids)

    # remove duplicates
    exp_id_list = list(set(exp_ids + exp_ids_from_batch_ids))

    if args.batchName is None:
        return exp_id_list

    # case: args.batchName is provided
    batch = BatchDataStore.get_batch_by_name(args.batchName)
    if batch:
        exp_ids_from_batch = batch.get_experiment_ids()

        print("\nBatch with name %s already exists and contains the following experiment(s):\n" % args.batchName)
        print '\n'.join([' - %s' % exp_id for exp_id in exp_ids_from_batch])

        if len(exp_id_list) > 0:
            var = raw_input('\nDo you want to [O]verwrite, [M]erge, or [C]ancel:  ')
            # print "You selected '%s'" % var
            if var == 'O':
                # clear existing experiments associated with this Batch
                BatchDataStore.clear_batch(batch)
                # the existing batch maps to new experiment list
                exp_id_list = list(set(exp_ids + exp_ids_from_batch_ids))
            elif var == 'M':
                # collect 'new' experiments to be added to the existing batch
                exp_id_list = list(set(exp_ids + exp_ids_from_batch_ids) - set(exp_ids_from_batch))
            elif var == 'C':
                exit()
            else:
                print "You selected '%s'" % var
                exit()
        else:
            # no asking, just process the given batch!
            exp_id_list = exp_ids_from_batch
    else:
        if len(exp_id_list) == 0:
            print 'Batch %s given is new, please provide experiments to analyze.' % args.batchName
            exit()

    return exp_id_list


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


def reload_experiments(exp_ids, try_sync=True):
    """
    Return the experiment (for given expId) or most recent experiment
    """
    exp_list = []
    for exp_id in exp_ids:

        exp = DataStore.get_most_recent_experiment(exp_id)
        if not exp and try_sync and exp_id:
            try:
                exp = retrieve_experiment(exp_id, verbose=False)
            except:
                exp = None

        if not exp:
            logger.error("No experiment found with the ID '%s' Locally or in COMPS. Exiting..." % exp_id)
            exit()

        exp_list.append(exp)

    return exp_list


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
        print "/!\\ BATCH WARNING /!\\"
        print 'Too many batch names are provided: %s' % unknownArgs
        exit()

    batches = None
    if args.batchId and len(unknownArgs) > 0:
        print "/!\\ BATCH WARNING /!\\"
        print 'Both batchId and batchName are provided. We will ignore both and list all batches in DB!\n'
        batches = BatchDataStore.get_batch_list()
    elif args.batchId:
        batches = BatchDataStore.get_batch_list(args.batchId)
    elif len(unknownArgs) > 0:
        batches = BatchDataStore.get_batch_list_by_name(unknownArgs[0])
    else:
        batches = BatchDataStore.get_batch_list()

    display_batch(batches)


def display_batch(batches):
    if batches:
        print '---------- Batch(s) in DB -----------'
        if isinstance(batches, list):
            for batch in batches:
                print '%s (id=%s, count=%s)' % (batch.name, batch.id, len(batch.experiments))
                for exp in batch.experiments:
                    print ' - %s' % exp.exp_id
            print '\nTotal: %s Batch(s)' % len(batches)
        else:
            print '%s (id=%s, count=%s)' % (batches.name, batches.id, len(batches.experiments))
            for exp in batches.experiments:
                print ' - %s' % exp.exp_id
            print '\nTotal: 1 Batch'
    else:
        print 'There is no Batch records in DB.'


def delete_batch(args, unknownArgs):
    """
    Delete a particular batch or all batches in DB
    """
    if len(unknownArgs) > 1:
        print 'Too many parameters are provided: %s' % unknownArgs
        exit()

    if args.batchId and len(unknownArgs) > 0:
        print "/!\\ BATCH WARNING /!\\"
        print 'Both batchId and batchName are provided. This action cannot take both!\n'
        exit()

    msg = ''
    if args.batchId:
        msg = 'Are you sure you want to delete the Batch %s (Y/n)? ' % args.batchId
    else:
        msg = 'Are you sure you want to delete all Batches (Y/n)? '

    choice = raw_input(msg)

    if choice != 'Y':
        print 'No action taken.'
        return
    else:
        BatchDataStore.delete_batch(args.batchId)
        print 'The Batch(s) have been deleted.'


def clear_batch(batchId=None, ask=False):
    """
    - de-attach all associated experiments from the given batch
      or
    - remove all empty batches
    """

    if batchId:
        msg = 'Are you sure you want to detach all associated experiments (Y/n)? '
    else:
        msg = 'Are you sure you want to remove all empty Batches (Y/n)? '

    if ask:
        choice = raw_input(msg)

        if choice != 'Y':
            print 'No action taken.'
            return
        else:
            if batchId:
                batch = BatchDataStore.get_batch_by_id(batchId)
                if batch:
                    BatchDataStore.clear_batch(batch)
            else:
                cnt = BatchDataStore.remove_empty_batch()
                if cnt > 0:
                    print 'The Total %s empty Batch(s) have been removed.' % cnt
    else:
        if batchId:
            batch = BatchDataStore.get_batch_by_id(batchId)
            if batch:
                BatchDataStore.clear_batch(batch)
                print 'The associated experiments have been detached.'
        else:
            cnt = BatchDataStore.remove_empty_batch()
            if cnt > 0:
                print 'The Total %s empty Batch(s) have been removed.' % cnt

