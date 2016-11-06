import time

from COMPS.Data import Experiment
from COMPS.Data.Simulation import SimulationState
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.Monitor import CompsSimulationMonitor
from simtools.SimulationRunner.BaseSimulationRunner import BaseSimulationRunner
from simtools.utils import init_logging

logger = init_logging('Runner')


class COMPSSimulationRunner(BaseSimulationRunner):

    def __init__(self, experiment, states, success, commission=True):
        logger.debug('Create COMPSSimulationRunner with experiment: %s, commission: %s'% (experiment.id,commission))
        super(COMPSSimulationRunner, self).__init__(experiment, states, success)

        if commission:
            self.run()
        else:
            self.monitor()

    def run(self):
        logger.debug('COMPS - Start Commissioning for experiment %s' % self.experiment.id)
        # Commission the experiment
        e = Experiment.get(id=self.experiment.exp_id)
        sims = e.get_simulations()
        for sim in sims:
            if sim.state == SimulationState.Created:
                sim.commission()
        self.monitor()

    def update_simulations_statuses(self,simids,states):
        for sim_id in simids:
            self.states.put({'sid':sim_id, 'status':states[sim_id], 'message':None, 'pid':None})

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
            except KeyError as e:
                logger.error('Exception in the COMPS Monitor for experiment %s' % self.experiment.id)
                logger.error(e)

            diff_list = [key for key in set(last_states).intersection(states) if last_states[key] != states[key]]
            logger.debug('COMPS - Difflist for experiment %s' % self.experiment.id)
            logger.debug(diff_list)

            if len(diff_list) > 0:
                try:
                    # Update the simulation status first
                    self.update_simulations_statuses(diff_list, states)

                    # loop again to take care of success if needed
                    for key in diff_list:
                        if states[key] == "Succeeded":
                            logger.debug("Simulation %s has succeeded, calling ths success callback" % key)
                            simulation = DataStore.get_simulation(key)
                            self.success(simulation)
                            logger.debug("Callback done for %s" % key)
                except Exception as e:
                    logger.error("Error in the COMPSRunner Monitor")
                    logger.error(e)

                last_states = states

            if CompsExperimentManager.status_finished(states):
                logger.debug('Stop monitoring for experiment %s because all simulations finished' % self.experiment.id)
                break

            time.sleep(10)
