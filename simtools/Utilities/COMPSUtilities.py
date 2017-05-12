from simtools.Utilities.General import is_remote_path, init_logging, get_md5, retry_function
logger = init_logging('Utils')

import os
import re

import shutil
from COMPS.Data import Experiment
from COMPS.Data import QueryCriteria
from COMPS.Data import Simulation
from COMPS.Data import Suite
from COMPS import Client
from COMPS.Data.Simulation import SimulationState

path_translations = {}
def translate_COMPS_path(path, setup=None):
    """
    Transform a COMPS path into fully qualified path.
    Supports:
    - $COMPS_PATH('BIN')
    - $COMPS_PATH('USER')
    - $COMPS_PATH('PUBLIC')
    - $COMPS_PATH('INPUT')
    - $COMPS_PATH('HOME')

    Query the COMPS Java client with the current environment to get the correct path.
    :param path: The COMPS path to transform
    :param setup: The setup to find user and environment
    :return: The absolute path
    """
    from COMPS import Client
    # Create the regexp
    regexp = re.search('.*(\$COMPS_PATH\((\w+)\)).*', path)

    # If no COMPS variable found -> return the path untouched
    if not regexp:
        return path

    # Check if we have a setup
    if not setup:
        from simtools.SetupParser import SetupParser
        setup = SetupParser()

    # Retrieve the variable to translate
    groups = regexp.groups()
    comps_variable = groups[1]

    # Is the path already cached
    if comps_variable in path_translations:
        abs_path = path_translations[comps_variable]
    else:
        # Prepare the variables we will need
        environment = setup.get('environment')

        #Q uery COMPS to get the path corresponding to the variable
        COMPS_login(setup.get('server_endpoint'))
        abs_path = Client.auth_manager().get_environment_macros(environment)[groups[1]]

        # Cache
        path_translations[comps_variable] = abs_path

    # Replace and return
    user = setup.get('user')
    return path.replace(groups[0], abs_path).replace("$(User)", user)


def stage_file(from_path, to_directory):
    if is_remote_path(from_path):
        logger.info('File is already staged; skipping copy to file-share')
        return from_path

    # Translate $COMPS path if needed
    to_directory_translated = translate_COMPS_path(to_directory)

    file_hash = get_md5(from_path)
    logger.info('MD5 of ' + os.path.basename(from_path) + ': ' + file_hash)

    # We need to use the translated path for the copy but return the untouched staged path
    stage_dir = os.path.join(to_directory_translated, file_hash)
    stage_path = os.path.join(stage_dir, os.path.basename(from_path))
    original_stage_path = os.path.join(to_directory,file_hash,os.path.basename(from_path))

    if not os.path.exists(stage_dir):
        try:
            os.makedirs(stage_dir)
        except:
            raise Exception("Unable to create directory: " + stage_dir)

    if not os.path.exists(stage_path):
        logger.info('Copying %s to %s (translated in: %s)' % (os.path.basename(from_path), to_directory, to_directory_translated))
        shutil.copy(from_path, stage_path)
        logger.info('Copying complete.')

    return original_stage_path

def COMPS_login(endpoint):
    try:
        am= Client.auth_manager()
    except:
        Client.login(endpoint)

    return Client

@retry_function
def get_experiment_by_id(exp_id):
    return Experiment.get(exp_id)

@retry_function
def get_simulation_by_id(sim_id):
    return Simulation.get(id=sim_id)

def get_experiments_per_user_and_date(user, limit_date):
    limit_date_str = limit_date.strftime("%Y-%m-%d")
    return Experiment.get(query_criteria=QueryCriteria().where('owner=%s,DateCreated>%s' % (user, limit_date_str)))


def get_experiments_by_name(name, user):
    return Experiment.get(query_criteria=QueryCriteria().where(['name~%s' % name, 'owner=%s' % user]))


def sims_from_experiment(e):
    return e.get_simulations(QueryCriteria().select(['id', 'state']).select_children('hpc_jobs'))


def experiment_needs_commission(e):
    return e.get_simulations(QueryCriteria().select(['id']).where("state=%d" % SimulationState.Created.value))


def sims_from_experiment_id(exp_id):
    return Simulation.get(query_criteria=QueryCriteria().select(['id', 'state']).where('experiment_id=%s' % exp_id))


def sims_from_suite_id(suite_id):
    exps = Experiment.get(query_criteria=QueryCriteria().where('suite_id=%s' % suite_id))
    sims = []
    for e in exps:
        sims += sims_from_experiment(e)
    return sims

def exps_for_suite_id(suite_id):
    try:
        return Experiment.get(query_criteria=QueryCriteria().where('suite_id=%s' % suite_id))
    except:
        return None


def experiment_is_running(e):
    for sim in e.get_simulations():
        if not sim.state in (SimulationState.Succeeded, SimulationState.Failed,
                             SimulationState.Canceled, SimulationState.Created, SimulationState.CancelRequested):
            return True
    return False


def workdirs_from_simulations(sims):
    return {str(sim.id): sim.hpc_jobs[-1].working_directory for sim in sims}


def workdirs_from_experiment_id(exp_id, experiment=None):
    e = experiment or Experiment.get(exp_id)
    sims = sims_from_experiment(e)
    return workdirs_from_simulations(sims)


def workdirs_from_suite_id(suite_id):
    # print('Simulation working directories for SuiteId = %s' % suite_id)
    s = Suite.get(suite_id)
    exps = s.get_experiments(QueryCriteria().select('id'))
    sims = []
    for e in exps:
        sims.extend(sims_from_experiment(e))
    return workdirs_from_simulations(sims)


def delete_suite(suite_id):
    s = Suite.get(suite_id)
    try:
        s.delete()
    except Exception as e:
        print "Could not delete suite %s" % suite_id
