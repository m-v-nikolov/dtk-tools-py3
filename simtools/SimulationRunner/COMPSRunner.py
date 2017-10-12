import time

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.Monitor import CompsSimulationMonitor
from simtools.SimulationRunner.BaseSimulationRunner import BaseSimulationRunner
from simtools.Utilities.COMPSUtilities import experiment_needs_commission, get_experiment_by_id, get_simulation_by_id, \
    COMPS_login
from COMPS.Data.Simulation import SimulationState
from simtools.Utilities.General import init_logging
logger = init_logging('Runner')


class COMPSSimulationRunner(BaseSimulationRunner):
    def __init__(self, experiment, states, success):
        logger.debug('Create COMPSSimulationRunner with experiment: %s' % experiment.id)
        super(COMPSSimulationRunner, self).__init__(experiment, states, success)

        # Check if we need to commission
        COMPS_login(experiment.endpoint)
        e = get_experiment_by_id(self.experiment.exp_id)

        if experiment_needs_commission(e):
            logger.debug('COMPS - Start Commissioning for experiment %s' % self.experiment.id)
            # Commission the experiment
            e.commission()

        self.monitor()

    def run(self):
        pass

    def update_simulations_statuses(self,simids,states):
        for sim_id in simids:
            self.states.put({'sid': sim_id, 'status':states[sim_id], 'message':None, 'pid':None})

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
            logger.debug('COMPS - Waiting loop')
            try:
                states, _ = monitor.query()
                if states == {}:
                    # No states returned... Consider failed
                    states = {sim_id:SimulationState.Failed for sim_id in last_states.keys()}
            except Exception as e:
                logger.error('Exception in the COMPS Monitor for experiment %s' % self.experiment.id)
                logger.error(e)

            # Create the diff list
            # This list holds the ids of simulations that changed since last loop
            # Also include eventual created simulations since last time
            diff_list = [key for key in states if (key in last_states and last_states[key] != states[key]) or states[key] == SimulationState.Created]

            logger.debug('COMPS - Difflist for experiment %s' % self.experiment.id)
            logger.debug(diff_list)

            if len(diff_list) > 0:
                try:
                    # Update the simulation status first
                    self.update_simulations_statuses(diff_list, states)

                    # loop again to take care of success if needed
                    for key in diff_list:
                        if states[key] == SimulationState.Succeeded:
                            logger.debug("Simulation %s has succeeded, calling ths success callback" % key)
                            simulation = DataStore.get_simulation(key)
                            self.success(simulation)
                            logger.debug("Callback done for %s" % key)
                        if states[key] == SimulationState.Created:
                            # If we find a simulation created but not commissioned -> run it!
                            # This case can happen when simulations are added at a later time
                            logger.debug("Found a simulation not commissioned: %s. Run it!" % key)
                            sim = get_simulation_by_id(key)
                            sim.commission()

                except Exception as e:
                    logger.error("Error in the COMPSRunner Monitor")
                    logger.error(e)

                last_states = states

            if CompsExperimentManager.status_finished(states):
                logger.debug('Stop monitoring for experiment %s because all simulations finished' % self.experiment.id)
                break

            time.sleep(2 * self.MONITOR_SLEEP)
