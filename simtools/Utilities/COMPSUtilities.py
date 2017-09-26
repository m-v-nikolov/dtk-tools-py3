import zipfile

from simtools.Utilities.General import init_logging, get_md5, retry_function

logger = init_logging('Utils')

import os
import re

import shutil
from COMPS.Data import Experiment, AssetCollection
from COMPS.Data import QueryCriteria
from COMPS.Data import Simulation
from COMPS.Data import Suite
from COMPS import Client
from COMPS.Data.Simulation import SimulationState

from simtools.SetupParser import SetupParser

path_translations = {}


def translate_COMPS_path(path):
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

    # Retrieve the variable to translate
    groups = regexp.groups()
    comps_variable = groups[1]

    # Is the path already cached
    if comps_variable in path_translations:
        abs_path = path_translations[comps_variable]
    else:
        with SetupParser.TemporarySetup('HPC') as setup:
            # Prepare the variables we will need
            environment = setup.get('environment')

            # Q uery COMPS to get the path corresponding to the variable
            COMPS_login(setup.get('server_endpoint'))
            abs_path = Client.auth_manager().get_environment_macros(environment)[groups[1]]

        # Cache
        path_translations[comps_variable] = abs_path

    # Replace and return
    with SetupParser.TemporarySetup() as setup:
        user = setup.get('user')

    return path.replace(groups[0], abs_path).replace("$(User)", user)


def stage_file(from_path, to_directory):
    # Translate $COMPS path if needed
    to_directory_translated = translate_COMPS_path(to_directory)

    file_hash = str(get_md5(from_path))
    logger.info('MD5 of ' + os.path.basename(from_path) + ': ' + file_hash)

    # We need to use the translated path for the copy but return the untouched staged path
    stage_dir = os.path.join(to_directory_translated, file_hash)
    stage_path = os.path.join(stage_dir, os.path.basename(from_path))
    original_stage_path = os.path.join(to_directory, file_hash, os.path.basename(from_path))

    if not os.path.exists(stage_dir):
        try:
            os.makedirs(stage_dir)
        except:
            raise Exception("Unable to create directory: " + stage_dir)

    if not os.path.exists(stage_path):
        logger.info('Copying %s to %s (translated in: %s)' % (
        os.path.basename(from_path), to_directory, to_directory_translated))
        shutil.copy(from_path, stage_path)
        logger.info('Copying complete.')

    return original_stage_path


def COMPS_login(endpoint):
    try:
        am = Client.auth_manager()
    except:
        Client.login(endpoint)

    return Client


def get_asset_collection(collection_id_or_name, query_criteria=None):
    if not collection_id_or_name: return None

    query_criteria = query_criteria or QueryCriteria().select_children('assets')
    # Try by id first
    collection = get_asset_collection_by_id(collection_id_or_name, query_criteria)
    if collection: return collection

    # And by name
    collection = get_asset_collection_by_tag("Name", collection_id_or_name, query_criteria)
    return collection


def get_asset_collection_by_id(collection_id, query_criteria=None):
    query_criteria = query_criteria or QueryCriteria().select_children('assets')
    try:
        return AssetCollection.get(collection_id, query_criteria)
    except (RuntimeError, ValueError):
        return None


def is_comps_alive(endpoint):
    import requests
    r = requests.get(endpoint)
    return r.status_code == 200


def get_asset_collection_by_tag(tag_name, tag_value, query_criteria=None):
    """
    Looks to see if a collection id exists for a given collection tag
    :param collection_tag: An asset collection tag that uniquely identifies an asset collection
    :return: An asset collection id if ONE match is found, else None (for 0 or 2+ matches)
    """
    query_criteria = query_criteria or QueryCriteria().select_children('assets')
    query_criteria.where_tag('%s=%s' % (tag_name, tag_value))
    result = AssetCollection.get(query_criteria=query_criteria)
    if len(result) >= 1: return result[0]
    return None


def download_asset_collection(collection, output_folder):
    if not isinstance(collection, AssetCollection):
        collection = AssetCollection.get(collection, query_criteria=QueryCriteria().select_children('assets'))

    # Get the files
    if len(collection.assets) > 0:

        # Download the collection as zip
        zip_path = os.path.join(output_folder, 'temp.zip')
        with open(zip_path, 'wb') as outfile:
            outfile.write(collection.retrieve_as_zip())

        # Extract it
        zip_ref = zipfile.ZipFile(zip_path, 'r')
        zip_ref.extractall(output_folder)
        zip_ref.close()

        # Delete the temporary zip
        os.remove(zip_path)


@retry_function
def get_experiment_by_id(exp_id, query_criteria=None):
    return Experiment.get(exp_id, query_criteria=query_criteria)


@retry_function
def get_simulation_by_id(sim_id, query_criteria=None):
    return Simulation.get(id=sim_id, query_criteria=query_criteria)


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


def get_semaphore():
    return Simulation.get_save_semaphore()


def experiment_is_running(e):
    for sim in e.get_simulations():
        if not sim.state in (SimulationState.Succeeded, SimulationState.Failed,
                             SimulationState.Canceled, SimulationState.Created, SimulationState.CancelRequested):
            return True
    return False


def workdirs_from_simulations(sims):
    return {str(sim.id): sim.hpc_jobs[-1].working_directory for sim in sims if sim.hpc_jobs}


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


def create_suite(suite_name):
    suite = Suite(suite_name)
    suite.save()
    return str(suite.id)


def delete_suite(suite_id):
    try:
        s = Suite.get(suite_id)
        s.delete()
    except Exception as e:
        print "Could not delete suite %s" % suite_id
