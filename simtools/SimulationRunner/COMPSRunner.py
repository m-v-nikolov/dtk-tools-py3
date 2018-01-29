import time

from COMPS.Data.Simulation import SimulationState

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.Monitor import CompsSimulationMonitor
from simtools.SimulationRunner.BaseSimulationRunner import BaseSimulationRunner
from simtools.Utilities.COMPSUtilities import experiment_needs_commission, COMPS_login
from simtools.Utilities.General import init_logging

logger = init_logging('Runner')


class COMPSSimulationRunner(BaseSimulationRunner):
    def __init__(self, experiment, comps_experiment):
        logger.debug('Create COMPSSimulationRunner with experiment: %s' % experiment.id)
        super(COMPSSimulationRunner, self).__init__(experiment)

        # Check if we need to commission
        COMPS_login(experiment.endpoint)
        self.comps_experiment = comps_experiment

        if experiment_needs_commission(self.comps_experiment):
            logger.debug('COMPS - Start Commissioning for experiment %s' % self.experiment.id)
            # Commission the experiment
            self.comps_experiment.commission()

        self.monitor()

    def run(self):
        pass

    def monitor(self):
        logger.debug('COMPS - Start Monitoring for experiment %s' % self.experiment.id)
        # Until done, update the status
        last_states = dict()
        for simulation in self.experiment.simulations:
            last_states[simulation.id] = simulation.status

        # Create the monitor
        monitor = CompsSimulationMonitor(self.experiment.exp_id, None, self.experiment.endpoint)

        # Until done, update the status
        while True:
            try:
                states, _ = monitor.query()
                if states == {}:
                    # No states returned... Consider failed
                    states = {sim_id:SimulationState.Failed for sim_id in last_states.keys()}
            except Exception as e:
                logger.error('Exception in the COMPS Monitor for experiment %s' % self.experiment.id)
                logger.error(e)

            # Only update the simulations that changed since last check
            # We are also including simulations that were not present (in case we add some later)
            DataStore.batch_simulations_update(list({"sid": key, "status":states[key].name} for key in states if (key in last_states and last_states[key] != states[key]) or key not in last_states))

            # Store the last state
            last_states = states

            if CompsExperimentManager.status_finished(states):
                logger.debug('Stop monitoring for experiment %s because all simulations finished' % self.experiment.id)
                break

            time.sleep(self.MONITOR_SLEEP)
