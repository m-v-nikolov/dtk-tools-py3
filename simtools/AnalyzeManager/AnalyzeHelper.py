import os
import sys
from importlib import import_module

from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore
from simtools.DataAccess.Schema import Batch, Experiment, Simulation
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_object, retrieve_simulation
from simtools.Utilities.General import init_logging, retrieve_item
from simtools.Utilities.Initialization import load_config_module

logger = init_logging('Commands')


def analyze(args, unknownArgs, builtinAnalyzers):
    # validate parameters
    if args.config_name is None:
        logger.error('Please provide Analyzer (-a or --config_name).')
        exit()

    # Retrieve what we need
    itemids = args.itemids
    batch_name = args.batch_name

    # collect all experiments and simulations
    exp_dict, sim_dict = collect_experiments_simulations(itemids)

    # consider batch existing case
    exp_dict, sim_dict = consolidate_experiments_with_options(exp_dict, sim_dict, batch_name)

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
    analyzeManager = AnalyzeManager(exp_list=exp_dict.values(), sim_list=sim_dict.values(), analyzers=analyzers)

    exp_ids_to_be_saved = list(set(exp_dict.keys()) - set(analyzeManager.experiments_simulations.keys()))
    exp_to_be_saved = [exp_dict[exp_id] for exp_id in exp_ids_to_be_saved]

    # if batch name exists, always save experiments
    if batch_name:
        # save/create batch
        save_batch(batch_name, exp_to_be_saved, sim_dict.values())
    # Only create a batch if we pass more than one experiment or simulation in total
    elif len(exp_dict) + len(sim_dict) > 1:
        # check if there is any existing batch containing the same experiments
        batch_existing = check_existing_batch(exp_dict, sim_dict)

        if batch_existing is None:
            # save/create batch
            save_batch(batch_name, exp_to_be_saved, sim_dict.values())
        else:
            # display the existing batch
            logger.info('\nBatch: %s (id=%s)' % (batch_existing.name, batch_existing.id))

    # start to analyze
    analyzeManager.analyze()

    # remove empty batches
    clean_batch()


def check_existing_batch(exp_dict, sim_dict):
    exp_ids_list = exp_dict.keys()
    sim_ids_list = sim_dict.keys()
    batch_list = DataStore.get_batch_list()

    for batch in batch_list:
        batch_exp_ids = batch.get_experiment_ids()
        batch_sim_ids = batch.get_simulation_ids()
        if compare_two_ids_list(exp_ids_list, batch_exp_ids) and compare_two_ids_list(sim_ids_list, batch_sim_ids):
            return batch

    return None


def compare_two_ids_list(ids_1, ids_2):
    return len(ids_1) == len(ids_2) and set(ids_1) == set(ids_2)


def save_batch(batch_name=None, exp_list=None, sim_list=None):
    if not exp_list and not sim_list:
        logger.info('Please provide some experiment(s)/simulation(s) to analyze.')
        exit()

    # Try to get the batch based on name if provided
    batch = DataStore.get_batch_by_name(batch_name) if batch_name else None

    # No batches were found, need to create a new one
    if not batch:
        batch = Batch()
        batch.name = batch_name

    # add experiments
    batch.experiments.extend(exp_list)

    # add simulations
    batch.simulations.extend(sim_list)

    # Save
    DataStore.save_batch(batch)

    logger.info('\nBatch: %s (id=%s) saved!' % (batch.name, batch.id))

    return batch


def create_batch(batch_name=None, itemsids=None):
    """
    create or use existing batch
    """
    # collect all experiments
    exp_dict, sim_dict = collect_experiments_simulations(itemsids)

    # consider batch existing case
    exp_dict, sim_dict = consolidate_experiments_with_options(exp_dict, sim_dict, batch_name)

    # save/create batch
    save_batch(batch_name, exp_dict.values(), sim_dict.values())


def consolidate_experiments_with_options(exp_dict, sim_dict, batch_name=None):
    # if batch name exists, always save experiments
    if batch_name is None:
        return exp_dict, sim_dict

    batch = DataStore.get_batch_by_name(batch_name)
    if batch:
        batch_exp_id_list = batch.get_experiment_ids()
        batch_sim_id_list = batch.get_simulation_ids()

        exp_diff = not compare_two_ids_list(exp_dict.keys(), batch_exp_id_list)
        sim_diff = not compare_two_ids_list(sim_dict.keys(), batch_sim_id_list)

        if exp_diff or sim_diff:
            # confirm only if existing batch contains different experiments
            print("\nBatch with name {} already exists and contains the following:\n".format(batch_name))
            print(batch)

            if exp_dict or sim_dict:
                var = input('\nDo you want to [O]verwrite, [M]erge, or [C]ancel:  ')
                # print "You selected '%s'" % var
                if var == 'O':
                    # clear existing experiments associated with this Batch
                    DataStore.clear_batch(batch)
                    return exp_dict, sim_dict
                elif var == 'M':
                    return exp_dict, sim_dict
                elif var == 'C':
                    exit()
                else:
                    logger.error("Option '%s' is invalid..." % var)
                    exit()

    return exp_dict, sim_dict


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


def collect_experiments_simulations(ids):
    experiments = dict()
    simulations = dict()

    if not ids: return experiments, simulations

    # For each, treat it differently depending on what it is
    for itemid in ids:
        item = retrieve_item(itemid)
        # We got back a list of experiment (itemid was a suite)
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
            simulations.update({i.id: retrieve_simulation(i.id) for i in item.simulations})

    return experiments, simulations


def check_status(exp_list):
    for exp in exp_list:
        if not exp.is_successful():
            logger.warning('Not all experiments have finished successfully yet...')
            exp_manager = ExperimentManagerFactory.from_experiment(exp)
            exp_manager.print_status()
            exit()


def list_batch(id_or_name=None):
    """
        List Details of Batches from local database
    """

    batches = DataStore.get_batch_list(id_or_name)

    if batches is None:
        # Batches still none probably didnt exist
        print("No batches idendified by {} could be found in the database...".format(id_or_name))
        exit()

    # Display
    if batches:
        print('---------- Batch(s) in DB -----------')
        if isinstance(batches, list):
            for batch in batches:
                print(batch)
            print('\nTotal: %s Batch(s)' % len(batches))
    else:
        print('There is no Batch records in DB.')


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
