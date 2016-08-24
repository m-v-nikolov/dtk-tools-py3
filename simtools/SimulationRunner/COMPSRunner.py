import json
import os
import time

from simtools.DataAccess.DataStore import DataStore
from simtools.Monitor import CompsSimulationMonitor
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
if __name__ == "__main__":

    import sys

    # Retrieve the info from the command line
    exp_id = sys.argv[1]

    # Retrieve the experiment
    current_exp = DataStore.get_experiment(exp_id)

    # Imports for COMPS
    os.environ['COMPS_REST_HOST'] = current_exp.endpoint
    from pyCOMPS import pyCOMPS

    # Until done, update the status
    last_states = dict()
    for simulation in current_exp.simulations:
        last_states[simulation.id] = simulation.status

    sims_update = list()
    while True:
        states, msgs = CompsSimulationMonitor(current_exp.exp_id, current_exp.suite_id, current_exp.endpoint).query()

        last_states_set = last_states
        diff_list = [key for key in set(last_states_set).intersection(states) if last_states[key] != states[key]]
        if len(diff_list) > 0:
            for key in diff_list:
                sims_update.append({"sid": key, "status": states[key]})

            last_states = states

            DataStore.batch_simulations_update(sims_update)
            # Empty the batch
            sims_update = list()

        if CompsExperimentManager.status_finished(states):
            current_exp = DataStore.get_experiment(exp_id)
            current_exp.experiment_runner_id = None
            DataStore.save_experiment(current_exp, verbose=False)
            break

        time.sleep(3)
