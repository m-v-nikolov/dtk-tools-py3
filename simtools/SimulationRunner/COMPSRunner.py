import json
import os
import threading

import dill
import pickle
import time
import sys
from simtools.DataAccess.DataStore import DataStore
from simtools.Monitor import CompsSimulationMonitor
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager

if __name__ == "__main__":
    # Retrieve the info from the command line
    exp_id = sys.argv[1]
    max_threads = int(sys.argv[2])

    # Retrieve the experiment
    current_exp = DataStore.get_experiment(exp_id)
    analyzers = [pickle.loads(analyzer.analyzer) for analyzer in current_exp.analyzers]

    parsers = {}
    max_threads = threading.Semaphore(max_threads)

    # Imports for COMPS
    os.environ['COMPS_REST_HOST'] = current_exp.endpoint
    from pyCOMPS import pyCOMPS

    # Until done, update the status
    last_states = dict()
    for simulation in current_exp.simulations:
        last_states[simulation.id] = simulation.status

    sims_update = list()

    # Until done, update the status
    while True:
        try:
            states, msgs = CompsSimulationMonitor(current_exp.exp_id, current_exp.suite_id, current_exp.endpoint).query()
        except Exception as e:
            print e
            break

        last_states_set = last_states
        diff_list = [key for key in set(last_states_set).intersection(states) if last_states[key] != states[key]]
        if len(diff_list) > 0:
            for key in diff_list:
                sims_update.append({"sid": key, "status": states[key], "message":msgs[key], "pid":None})
                if states[key] == "Succeeded":
                    simulation = DataStore.get_simulation(key)
                    # Called when a simulation finishes
                    filtered_analyses = [a for a in analyzers if a.filter(simulation.tags)]
                    if not filtered_analyses:
                        continue

                    max_threads.acquire()

                    from simtools.OutputParser import CompsDTKOutputParser

                    parser = CompsDTKOutputParser(current_exp.get_path(),
                                                  simulation.id,
                                                  simulation.tags,
                                                  filtered_analyses,
                                                  max_threads)
                    parser.start()
                    parsers[parser.sim_id] = parser

            last_states = states

            DataStore.batch_simulations_update(sims_update)
            # Empty the batch
            sims_update = list()

        if CompsExperimentManager.status_finished(states):
            current_exp = DataStore.get_experiment(exp_id)
            current_exp.experiment_runner_id = None
            DataStore.save_experiment(current_exp, verbose=False)

            if len(analyzers) != 0:
                # We are all done, finish analyzing
                for p in parsers.values():
                    p.join()

                for a in analyzers:
                    a.combine(parsers)
                    a.finalize()
            break

        time.sleep(5)
