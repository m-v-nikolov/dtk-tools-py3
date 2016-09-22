import threading
import time
from Queue import Queue
from collections import OrderedDict

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.utils import nostdout


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

        time.sleep(4)


if __name__ == "__main__":
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
    plotting_threads = []

    while True:
        # Retrieve the active LOCAL experiments
        active_experiments = DataStore.get_active_experiments()

        # Create all the managers
        for experiment in active_experiments:
            if not managers.has_key(experiment.id):
                with nostdout():
                    manager = ExperimentManagerFactory.from_experiment(experiment)
                managers[experiment.id] = manager
                manager.maxThreadSemaphore = analysis_semaphore
                if manager.location == "LOCAL": manager.local_queue = local_queue

        # Check every one of them
        for manager in managers.values():
            # If the runners have not been created -> create them
            if not manager.runner_created:
                manager.commission_simulations(update_states)

            # If the manager is done -> analyze
            if manager.finished():
                # Analyze
                manager.analyze_experiment()

                if manager.plotting_thread:
                    plotting_threads.append(manager.plotting_thread)

                # After analysis delete the manager from the list
                del managers[manager.experiment.id]

        # Cleanup the analyze thread list
        for pthread in plotting_threads:
            if not pthread.is_alive(): plotting_threads.remove(pthread)

        # No more active managers  -> Exit if our analyzers threads are done
        if len(managers) == 0 and len(plotting_threads) == 0: break

        time.sleep(5)