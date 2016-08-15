import os
import time

from simtools.DataAccess.DataStore import DataStore
from simtools.Monitor import CompsSimulationMonitor

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
    while (True):
        states, msgs  = CompsSimulationMonitor(current_exp.exp_id, current_exp.suite_id, current_exp.endpoint).query()
        print states
        time.sleep(3)
