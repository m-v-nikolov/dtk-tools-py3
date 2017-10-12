import os
import gc
import multiprocessing
import sys
# Add the tools to the path
sys.path.append(os.path.abspath('..'))
import threading
import time
import traceback
from collections import OrderedDict
from datetime import datetime

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.Utilities.General import init_logging
from simtools.Utilities.COMPSUtilities import is_comps_alive

logger = init_logging('Overseer')


def SimulationStateUpdater(states):
    while True:
        logger.debug("Simulation update function")
        if states:
            try:
                while not states.empty():
                    batch = []
                    while len(batch) < 250 and not states.empty():
                        batch.append(states.get())
                    DataStore.batch_simulations_update(batch)
            except Exception as e:
                logger.error("Exception in the status updater")
                logger.error(e)

        time.sleep(3)


def LogCleaner():
    # Get the last time a cleanup happened
    last_cleanup = DataStore.get_setting('last_log_cleanup')
    if not last_cleanup or (datetime.today() - datetime.strptime(last_cleanup.value.split(' ')[0],'%Y-%m-%d')).days > 1:
        # Do the cleanup
        from simtools.DataAccess.LoggingDataStore import LoggingDataStore
        LoggingDataStore.log_cleanup()
        DataStore.save_setting(DataStore.create_setting(key='last_log_cleanup', value=datetime.today()))

if __name__ == "__main__":

    logger.debug('Start Overseer pid: %d' % os.getpid())
    
    # we technically don't care about full consistency of SetupParser with the original dtk command, as experiments
    # have all been created. We can grab 'generic' max_local_sims / max_threads
    SetupParser.init() # default block
    max_local_sims = int(SetupParser.get('max_local_sims'))
    max_analysis_threads = int(SetupParser.get('max_threads'))

    # Create the queue
    local_queue = multiprocessing.Queue(max_local_sims)

    managers = OrderedDict()

    # Queue to be shared among all runners in order to update the individual simulation states in the DB
    states_queue = multiprocessing.Queue()
    update_state_thread = threading.Thread(target=SimulationStateUpdater, args=(states_queue,))
    update_state_thread.daemon = True
    update_state_thread.start()

    # Take this opportunity to cleanup the logs
    lc = threading.Thread(target=LogCleaner)
    lc.start()

    # will hold the analyze threads
    analysis_threads = []
    count = 0

    while True:
        # Retrieve the active LOCAL experiments
        active_experiments = DataStore.get_active_experiments()
        logger.debug('Waiting loop pass number %d, pid %d' % (count, os.getpid()))
        logger.debug('Active experiments')
        logger.debug(active_experiments)
        logger.debug('Managers')
        logger.debug(managers.keys())

        # Create all the managers
        for experiment in active_experiments:
            logger.debug("Looking for manager for experiment %s" % experiment.id)
            if experiment.id not in managers:
                logger.debug('Creating manager for experiment id: %s' % experiment.id)
                manager = None
                try:
                    sys.path.append(experiment.working_directory)
                    manager = ExperimentManagerFactory.from_experiment(experiment)
                except Exception as e:
                    logger.debug('Exception in creation manager for experiment %s' % experiment.id)
                    logger.debug(e)
                    logger.debug(traceback.format_exc())
                    # See what to do depending on what happened
                    if experiment.location == "HPC":
                        # Exit if we couldnt ping COMPS
                        if not is_comps_alive(experiment.endpoint):
                            logger.error("Exiting the Overseer because COMPS is not available!")
                            exit()
                        else:
                            # COMPS is alive, sync this particular experiment
                            try:
                                exp = retrieve_experiment(experiment.id, force_update=True)
                                manager = ExperimentManagerFactory.from_experiment(exp)
                            except:
                                logger.debug("Experiment %s deleted from local DB!" % experiment.id)
                if manager:
                    if manager.location == "LOCAL": manager.local_queue = local_queue
                    managers[experiment.id] = manager

            else:
                # Refresh the experiment
                logger.debug("Found manager for experiment %s" % experiment.id)
                managers[experiment.id].experiment = experiment

        # Check every one of them
        logger.debug("Checking experiment managers. There are %d of them. pid: %d" % (len(managers), os.getpid()))
        managers_to_delete = []
        for exp_id, manager in managers.items():
            logger.debug("Checking manager %s" % exp_id)
            if manager.finished():
                logger.debug('Manager for experiment id: %s is done' % exp_id)
                # Analyze
                # For now commented out - Will be reinstated when run_and_analyze comes back
                # athread = multiprocessing.Thread(target=manager.analyze_experiment)
                # athread.start()
                # analysis_threads.append(athread)

                # After analysis delete the manager from the list
                # Do it after the loop to not change the dict while iterating over it
                managers_to_delete.append(exp_id)
            else:
                # Refresh the experiment first
                manager.refresh_experiment()
                logger.debug('Commission simulations as needed for experiment id: %s' % exp_id)
                n_commissioned_sims = manager.commission_simulations(states_queue)
                logger.debug('Experiment done (re)commissioning %d simulation(s)' % n_commissioned_sims)

        # Delete the managers that needs to be deleted
        for exp_id in managers_to_delete:
            del managers[exp_id]
        gc.collect()

        # Cleanup the analyze thread list
        for ap in analysis_threads:
            if not ap.is_alive(): analysis_threads.remove(ap)
        logger.debug("Analysis thread: %s" % analysis_threads)

        # No more active managers -> Exit if our analyzer threads are done
        # Do not use len() to not block anything
        if managers == OrderedDict() and analysis_threads == []: break

        time.sleep(10)
        count += 1

logger.debug('No more work to do, Overseer pid: %d exiting...' % os.getpid())
