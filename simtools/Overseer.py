import logging
import multiprocessing
import threading
import time
from Queue import Queue
from collections import OrderedDict

import sys
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.utils import init_logging

logger = init_logging('Overseer')
lock = multiprocessing.Lock()

def SimulationStateUpdater(states, loop=True):
    while True:
        if states:
            lock.acquire()
            try:
                batch = []
                # First retrieve our simulation state
                for db_state in DataStore.get_simulation_states(states.keys()):
                    if db_state[1] in ('Succeeded','Failed','Canceled'):
                        continue
                    else:
                        new_state = states[db_state[0]]
                        batch.append({'sid':db_state[0], "status": new_state.status, "message":new_state.message, "pid":new_state.pid})

                DataStore.batch_simulations_update(batch)
                states.clear()
            except Exception as e:
                logger.error("Exception in the status updater")
                logger.error(e)
            finally:
                lock.release()
            if not loop: return

        time.sleep(5)


if __name__ == "__main__":
    logger.debug('Start Overseer')
    # Retrieve the threads number
    sp = SetupParser()
    max_local_sims = int(sp.get('max_local_sims'))
    max_analysis_threads = int(sp.get('max_threads'))

    # Create the queues and semaphore
    local_queue = Queue(max_local_sims)
    analysis_semaphore = threading.Semaphore(max_analysis_threads)

    update_states = {}
    managers = OrderedDict()

    # Start the simulation updater
    t1 = threading.Thread(target=SimulationStateUpdater, args=(update_states, True))
    t1.daemon = True
    t1.start()

    # will hold the analyze threads
    analysis_threads = []

    while True:
        # Retrieve the active LOCAL experiments
        active_experiments = DataStore.get_active_experiments()
        logger.debug('Waiting loop...')
        logger.debug('Active experiments')
        logger.debug(active_experiments)
        logger.debug('Managers')
        logger.debug(managers.keys())

        # Create all the managers
        for experiment in active_experiments:
            if not managers.has_key(experiment.id):
                logger.debug('Creation of manager for experiment id: %s' % experiment.id)
                try:
                    sys.path.append(experiment.working_directory)
                    manager = ExperimentManagerFactory.from_experiment(experiment)
                except Exception as e:
                    logger.error('Exception in creation manager for experiment %s' % experiment.id)
                    logger.error(e)
                    exit()
                managers[experiment.id] = manager
                manager.maxThreadSemaphore = analysis_semaphore
                if manager.location == "LOCAL": manager.local_queue = local_queue

        # Check every one of them
        for manager in managers.values():
            # If the runners have not been created -> create them
            if not manager.runner_created:
                logger.debug('Commission simulations for experiment id: %s' % manager.experiment.id)
                manager.commission_simulations(update_states, lock)
                logger.debug('Experiment done commissioning ? %s' % manager.runner_created)
                continue

            # If the manager is done -> analyze
            if manager.finished():
                logging.debug('Manager for experiment id: %s is done' % manager.experiment.id)
                # Analyze
                athread = threading.Thread(target=manager.analyze_experiment)
                athread.start()
                analysis_threads.append(athread)

                # After analysis delete the manager from the list
                del managers[manager.experiment.id]

        # Cleanup the analyze thread list
        for ap in analysis_threads:
            if not ap.is_alive(): analysis_threads.remove(ap)
        logger.debug("Analysis thread: %s" % analysis_threads)

        # No more active managers  -> Exit if our analzers threads are done
        # Do not use len() to not block anything
        if managers == OrderedDict() and analysis_threads == []: break

        time.sleep(5)

logger.debug('No more work to do, exiting...')