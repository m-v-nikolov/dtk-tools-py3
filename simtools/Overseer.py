import logging
import threading
import time
from Queue import Queue
from collections import OrderedDict

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.utils import init_logging

init_logging()
logger = logging.getLogger('Overseer Thread')

def SimulationStateUpdater(states, loop=True):
    while True:
        if states:
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
            if not loop: return

        time.sleep(5)


if __name__ == "__main__":
    logging.info('Start Overseer')
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
        logging.info('Overseer - Waiting')
        logging.info('Overseer - Active experiments')
        logging.info(active_experiments)
        logging.info('Overseer - Managers')
        logging.info(managers.keys())

        # Create all the managers
        for experiment in active_experiments:
            if not managers.has_key(experiment.id):
                logging.info('Overseer - Created manager for experiment id: %s' % experiment.id)
                try:
                    manager = ExperimentManagerFactory.from_experiment(experiment)
                except Exception as e:
                    logging.error('Exception in creation manager for experiment %s' % experiment.id)
                    logging.error(e)
                    exit()
                managers[experiment.id] = manager
                manager.maxThreadSemaphore = analysis_semaphore
                if manager.location == "LOCAL": manager.local_queue = local_queue

        # Check every one of them
        for manager in managers.values():
            # If the runners have not been created -> create them
            if not manager.runner_created:
                logging.info('Overseer - Commission simulations for experiment id: %s' % manager.experiment.id)
                manager.commission_simulations(update_states)
                logging.info('Overseer - Experiment done commissioning ? %s' % manager.runner_created)

            # If the manager is done -> analyze
            if manager.finished():
                logging.info('Overseer - Manager for experiment id: %s is done' % manager.experiment.id)
                # Analyze
                athread = threading.Thread(target=manager.analyze_experiment)
                athread.start()
                analysis_threads.append(athread)

                # After analysis delete the manager from the list
                del managers[manager.experiment.id]

        # Cleanup the analyze thread list
        for ap in analysis_threads:
            if not ap.is_alive(): analysis_threads.remove(ap)

        # No more active managers  -> Exit if our analyzers threads are done
        # Do not use len() to not block anything
        if managers == OrderedDict() and analysis_threads == []: break

        time.sleep(5)

logging.info('Overseer - No more work to do, exiting...')