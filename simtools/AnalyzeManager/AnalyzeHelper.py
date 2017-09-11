import json
import os
import sys
from importlib import import_module

from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore
from simtools.DataAccess.Schema import Batch, Experiment, Simulation
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.Utilities.General import init_logging, retrieve_item

logger = init_logging('Commands')


def analyze(args, unknownArgs, builtinAnalyzers):
    # logger.info('Analyzing results...')

    # validate parameters
    validate_parameters(args, unknownArgs)

    # collect all experiments and simulations
    exp_dict, sim_dict = collect_experiments_simulations(args)

    # consider batch existing case
    exp_dict, sim_dict = consolidate_experiments_with_options(args, exp_dict, sim_dict)

    # check status for each experiment
    if not args.force:
        check_status(exp_dict.values())

    # collect all analyzers
    analyzers = collect_analyzers(args, builtinAnalyzers)

    if not exp_dict and not sim_dict:
        # No experiment specified -> using latest experiment
        latest = DataStore.get_most_recent_experiment()
        exp_dict[latest.exp_id] = latest

    # create instance of AnalyzeManager
    analyzeManager = AnalyzeManager(exp_list=exp_dict.values(), sim_list=sim_dict.values(), analyzer_list=analyzers)

    # if batch name exists, always save experiments
    if args.batch_name:
        # save/create batch
        save_batch(args, exp_dict.values(), sim_dict.values())
    # Only create a batch if we pass more than one experiment or simulation in total
    elif len(exp_dict) + len(sim_dict) > 1:
        # check if there is any existing batch containing the same experiments
        batch_existing = check_existing_batch(exp_dict, sim_dict)

        if batch_existing is None:
            # save/create batch
            save_batch(args, exp_dict.values(), sim_dict.values())
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


def check_existing_batch(exp_dict, sim_dict):
    exp_ids_list = exp_dict.keys()
    sim_ids_list = sim_dict.keys()
    batch_list = DataStore.get_batch_list_by_id()

    for batch in batch_list:
        batch_exp_ids = batch.get_experiment_ids()
        batch_sim_ids = batch.get_simulation_ids()
        if compare_two_ids_list(exp_ids_list, batch_exp_ids) and compare_two_ids_list(sim_ids_list, batch_sim_ids):
            return batch

    return None


def compare_two_ids_list(ids_1, ids_2):
    return len(ids_1) == len(ids_2) and set(ids_1) == set(ids_2)


def save_batch(args, exp_list=None, sim_list=None):
    if len(exp_list) + len(sim_list) == 0:
        logger.info('Please provide some experiment(s)/simulation(s) to analyze.')
        exit()

    batch = DataStore.get_batch_by_name(args.batch_name)
    existing = True if batch else False

    # create a new Batch if not exists
    if batch is None:
        batch = Batch()

    # add experiments
    for exp in exp_list:
        # ok, SqlAlchemy won't add duplicated experiment
        batch.experiments.append(exp)

    # add simulations
    for sim in sim_list:
        # ok, SqlAlchemy won't add duplicated simulation
        batch.simulations.append(sim)

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
        create or use existing batch
    """
    # collect all experiments
    exp_dict, sim_dict = collect_experiments_simulations(args)

    # consider batch existing case
    exp_dict = consolidate_experiments_with_options(args, exp_dict)

    # save/create batch
    save_batch(args, exp_dict.values(), sim_dict.values())


def consolidate_experiments_with_options(args, exp_dict, sim_dict):
    # if batch name exists, always save experiments
    if args.batch_name is None:
        return exp_dict, sim_dict

    batch = DataStore.get_batch_by_name(args.batch_name)
    if batch:
        batch_exp_id_list = batch.get_experiment_ids()
        batch_sim_id_list = batch.get_simulation_ids()

        exp_diff = not compare_two_ids_list(exp_dict.values(), batch_exp_id_list)
        sim_diff = not compare_two_ids_list(sim_dict.values(), batch_sim_id_list)

        if exp_diff or sim_diff:

            # confirm only if existing batch contains different experiments
            logger.info(
                "\nBatch with name %s already exists and contains the following experiment(s)/simulation(s):\n" % args.batch_name)
            if len(batch_exp_id_list) > 0:
                logger.info('Experiment(s):')
                logger.info('\n'.join([' - %s' % exp_id for exp_id in batch_exp_id_list]))
            if len(batch_sim_id_list) > 0:
                logger.info('Simulation(s)')
                logger.info('\n'.join([' - %s' % sim_id for sim_id in batch_sim_id_list]))

            if exp_dict or sim_dict:
                var = raw_input('\nDo you want to [O]verwrite, [M]erge, or [C]ancel:  ')
                # print "You selected '%s'" % var
                if var == 'O':
                    # clear existing experiments associated with this Batch
                    DataStore.clear_batch(batch)
                    return exp_dict, sim_dict
                elif var == 'M':
                    # collect 'new' experiments to be added to the existing batch
                    for exp_id in batch_exp_id_list:
                        if not exp_dict.has_key(exp_id):
                            exp_dict[exp_id] = retrieve_experiment(exp_id)

                    # collect 'new' simulations to be added to the existing batch
                    for sim_id in batch_sim_id_list:
                        if not sim_dict.has_key(sim_id):
                            sim_dict[sim_id] = DataStore.get_simulation(sim_id)

                    return exp_dict, sim_dict
                elif var == 'C':
                    exit()
                else:
                    logger.error("Option '%s' is invalid..." % var)
                    exit()


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


def collect_simulations(args):
    simulations = dict()

    # retrieve ids
    ids = args.itemids

    if not ids:
        return simulations

    # For each, treat it differently depending on what it is
    for sid in ids:
        sim = DataStore.get_simulation(sid)
        simulations[sim.id] = sim

    return simulations


def collect_experiments_simulations(args):
    experiments = dict()
    simulations = dict()

    # retrieve ids
    ids = args.itemids

    if not ids: return experiments, simulations

    # For each, treat it differently depending on what it is
    for itemid in ids:
        item = retrieve_item(itemid)
        # We got back a list of experiment
        if isinstance(item, list):
            experiments.update({i.exp_id: i for i in item})
        elif isinstance(item, Experiment):
            experiments[item.exp_id] = item
        elif isinstance(item, Simulation):
            simulations[item.id] = item
        elif isinstance(item, Batch):
            # We have to retrieve_experiment even if we already have the experiment object
            # to make sure we are loading the simulations associated with it
            experiments.update({i.exp_id: retrieve_experiment(i.exp_id) for i in item.experiments})

    return experiments, simulations


def check_status(exp_list):
    for exp in exp_list:
        exp_manager = ExperimentManagerFactory.from_experiment(exp)
        exp_manager.analyzers = []
        states, msgs = exp_manager.get_simulation_status()
        if not exp_manager.status_succeeded(states):
            logger.warning('Not all jobs have finished successfully yet...')
            logger.info('Job states:')
            from simtools.Utilities.Encoding import GeneralEncoder
            logger.info(json.dumps(states, sort_keys=True, indent=4, cls=GeneralEncoder))
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
        List Details of Batches from local database
    """
    batches = None
    if args.id_or_name and len(unknownArgs) > 0:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('More than one Batch Id/Name are provided. We will ignore both and list all batches in DB!\n')
        batches = DataStore.get_batch_list_by_id()
    elif args.id_or_name:
        # consider id case first
        batches = DataStore.get_batch_list_by_id(args.id_or_name)
        # consider name case
        if batches is None:
            batches = DataStore.get_batch_list_by_name(args.id_or_name)
    else:
        # query all batches in DB
        batches = DataStore.get_batch_list_by_id(None)

    display_batch(batches)


def display_batch(batches):
    if batches:
        logger.info('---------- Batch(s) in DB -----------')
        if isinstance(batches, list):
            for batch in batches:
                logger.info('\n%s (id=%s, exp_count=%s, sim_count=%s)' % (batch.name, batch.id, len(batch.experiments), len(batch.simulations)))
                logger.info('Experiments:')
                for exp in batch.experiments:
                    logger.info(' - %s' % exp.exp_id)

                logger.info('Simulations:')
                for sim in batch.simulations:
                    logger.info(' - %s' % sim.id)
            logger.info('\nTotal: %s Batch(s)' % len(batches))
        else:
            logger.info('\n%s (id=%s, exp_count=%s, sim_count=%s)' % (batches.name, batches.id, len(batches.experiments), len(batches.simulations)))
            logger.info('Experiments:')
            for exp in batches.experiments:
                logger.info(' - %s' % exp.exp_id)

            logger.info('Simulations:')
            for sim in batches.simulations:
                logger.info(' - %s' % sim.id)
            logger.info('\nTotal: 1 Batch')
    else:
        logger.info('There is no Batch records in DB.')


def delete_batch(args, unknownArgs):
    """
        Delete a particular batch or all batches in DB
    """
    if args.batch_id and len(unknownArgs) > 0:
        logger.warning("/!\\ BATCH WARNING /!\\")
        logger.warning('It takes only 1 batch_id but more are provided.\n')
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


def clear_batch(args, unknownArgs, ask=False):
    """
        de-attach all associated experiments from the given batch
    """
    batch = DataStore.get_batch_by_id(args.id_or_name)

    if batch is None:
        batch = DataStore.get_batch_by_name(args.id_or_name)

    if batch is None:
        logger.info("The Batch given by '%s' doesn't exist! ." % args.id_or_name)
        exit()

    if ask:
        msg = 'Are you sure you want to detach all associated experiments (Y/n)? '
        choice = raw_input(msg)

        if choice != 'Y':
            logger.warning('No action taken.')
            return

    DataStore.clear_batch(batch)
    logger.info('The associated experiments have been detached.')


def clean_batch(ask=False):
    """
        remove all empty batches
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
