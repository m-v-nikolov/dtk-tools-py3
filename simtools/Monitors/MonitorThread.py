import threading
import time
from Queue import Queue
from collections import OrderedDict

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser


def SimulationStateUpdater(states, loop=True):
    while True:
        batch = [{'sid':id, "status": s.status, "message":s.message, "pid":s.pid} for id,s in states.iteritems()]
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
    t1 = threading.Thread(target=SimulationStateUpdater, args=(update_states, True))
    t1.daemon = True
    t1.start()

    managers = OrderedDict()

    while True:
        # Retrieve the active LOCAL experiments
        active_experiments = DataStore.get_active_experiments()

        # Create all the managers
        for experiment in active_experiments:
            if not managers.has_key(experiment.id):
                manager = ExperimentManagerFactory.from_experiment(experiment)
                managers[experiment.id] = manager
                manager.maxThreadSemaphore = analysis_semaphore
                if manager.location == "LOCAL": manager.local_queue = local_queue

        # No more active managers  -> Exit
        if len(managers) == 0: exit()

        for manager in managers.values():
            if not manager.runner_created:
                manager.commission_simulations(update_states)

            elif manager.finished():
                # Analyze
                manager.analyze()
                # Remove it from the list
                del managers[manager.experiment.id]

        time.sleep(5)
