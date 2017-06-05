from __future__ import print_function

from simtools.DataAccess.DataStore import DataStore
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSUtilities import get_experiment_by_id, COMPS_login
from simtools.Utilities.General import init_logging, utc_to_local

max_exp_name_len = 100

logger = init_logging('Utils')


def validate_exp_name(exp_name):
    if len(exp_name) > max_exp_name_len:
        logger.info(
            "The experiment name '%s' exceeds the max length %s, please adjust your experiment name. Exiting...",
            exp_name, max_exp_name_len)
        return False
    else:
        return True


def retrieve_experiment(exp_id, sync_if_missing=True, verbose=False, force_update=False):
    """
    Retrieve an experiment in the local database based on its id.
    Can call a sync if missing if the flag is true.
    :param exp_id: Id of the experiment to retrieve
    :param sync_if_missing: Should we try to sync if not present?
    :return: The experiment found
    """
    if not exp_id: raise Exception("Trying to retrieve an experiment without providing an experiment ID")

    # If we dont force the update -> look first in the DB
    exp = DataStore.get_experiment(exp_id)
    if exp:
        # If we have an experiment and we want to force the update -> delete it
        if not force_update:
            return exp
        else:
            DataStore.delete_experiment(exp)

    if not sync_if_missing:
        raise Exception('Experiment %s not found in the local database and sync disabled.' % exp_id)

    logger.info('Experiment with id %s not found in local database, trying sync.' % exp_id)
    endpoint = SetupParser.get(block='HPC', parameter='server_endpoint')
    exp = COMPS_experiment_to_local_db(exp_id, endpoint, verbose)

    if exp: return exp
    raise Exception("Experiment '%s' could not be retrieved." % exp_id)


def COMPS_experiment_to_local_db(exp_id, endpoint, verbose=False, save_new_experiment=True):
    """
    Return a DB object representing an experiment coming from COMPS.
    This function saves the newly retrieved experiment in the DB by default but this behavior can be changed by switching
    the save_new_experiment parameter allowing to return an experiment object and save later with a batch for example.
    :param exp_id:
    :param endpoint:
    :param verbose:
    :param save_new_experiment:
    :return:
    """
    # Make sure we are logged in
    COMPS_login(endpoint)

    # IF the experiment already exists and
    experiment = DataStore.get_experiment(exp_id)
    if experiment and experiment.is_done():
        if verbose:
            print("Experiment ('%s') already exists in local db." % exp_id)
        # Do not bother with finished experiments
        return None

    from COMPS.Data import QueryCriteria
    try:
        exp_comps = get_experiment_by_id(exp_id)
    except:
        if verbose:
            print("The experiment ('%s') doesn't exist in COMPS." % exp_id)
        return None

    # Case: experiment doesn't exist in local db
    if not experiment:
        # Cast the creation_date
        experiment = DataStore.create_experiment(exp_id=str(exp_comps.id),
                                                 suite_id=str(exp_comps.suite_id) if exp_comps.suite_id else None,
                                                 exp_name=exp_comps.name,
                                                 date_created=utc_to_local(exp_comps.date_created).replace(tzinfo=None),
                                                 location='HPC',
                                                 selected_block='HPC',
                                                 endpoint=endpoint)

    # Note: experiment may be new or comes from local db
    # Get associated simulations of the experiment
    sims = exp_comps.get_simulations(QueryCriteria().select(['id', 'state', 'date_created']).select_children('tags'))

    # Skip empty experiments or experiments that have the same number of sims
    if len(sims) == 0 or len(sims) == len(experiment.simulations):
        if verbose:
            if len(sims) == 0:
                print("Skip empty experiment ('%s')." % exp_id)
            elif len(sims) == len(experiment.simulations):
                print("Skip experiment ('%s') since local one has the same number of simulations." % exp_id)
        return None

    # Go through the sims and create them
    for sim in sims:
        # Create the simulation
        simulation = DataStore.create_simulation(id=str(sim.id),
                                                 status=sim.state, # this is already a SimulationState object
                                                 tags=sim.tags,
                                                 date_created=utc_to_local(sim.date_created).replace(tzinfo=None))
        # Add to the experiment
        experiment.simulations.append(simulation)

    # Save it to the DB
    if save_new_experiment: DataStore.save_experiment(experiment, verbose=verbose)

    return experiment