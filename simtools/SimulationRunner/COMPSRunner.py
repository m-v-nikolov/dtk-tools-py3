import os
import time

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.Monitor import CompsSimulationMonitor


class HPCSimulationCommissioner:
    def __init__(self, experiment, states, success, commission=True):
        self.experiment = experiment
        self.success = success
        self.states = states
        self.commission = commission
        self.run()


    def commission_experiment(self):
        from COMPS.Data import Experiment
        e = Experiment.GetById(self.experiment.exp_id)
        e.Commission()

    def run(self):
        # Imports for COMPS
        os.environ['COMPS_REST_HOST'] = self.experiment.endpoint

        # Commission the experiment if needed
        if self.commission:
            self.commission_experiment()

        # Until done, update the status
        last_states = dict()
        for simulation in self.experiment.simulations:
            last_states[simulation.id] = simulation.status

        # Until done, update the status
        while True:
            try:
                states, _ = CompsSimulationMonitor(self.experiment.exp_id, self.experiment.suite_id,
                                                      self.experiment.endpoint).query()
            except Exception as e:
                print e
                break

            diff_list = [key for key in set(last_states).intersection(states) if last_states[key] != states[key]]
            if len(diff_list) > 0:
                for key in diff_list:
                    # Create the simulation to send to the update
                    self.states[key] = DataStore.create_simulation(status=states[key])

                    if states[key] == "Succeeded":
                        simulation = DataStore.get_simulation(key)
                        self.success(simulation)

                last_states = states

            if CompsExperimentManager.status_finished(states):
                break

            time.sleep(5)