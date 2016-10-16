import os
import time

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.CompsExperimentManager import CompsExperimentManager
from simtools.Monitor import CompsSimulationMonitor
from simtools.SimulationRunner.BaseSimulationRunner import BaseSimulationRunner
from simtools.utils import init_logging

logger = init_logging('Runner')


class COMPSSimulationRunner(BaseSimulationRunner):

    def __init__(self, experiment, states, success, lock, commission=True):
        logger.debug('Create COMPSSimulationRunner with experiment: %s, commission: %s'% (experiment.id,commission))
        super(COMPSSimulationRunner, self).__init__(experiment, states, success, lock)

        if commission:
            self.run()
        else:
            self.monitor()

    def run(self):
        logger.debug('COMPS - Start Commissioning for experiment %s' % self.experiment.id)
        # Imports for COMPS
        os.environ['COMPS_REST_HOST'] = self.experiment.endpoint

        # Commission the experiment
        from COMPS.Data import Experiment
        e = Experiment.GetById(self.experiment.exp_id)
        e.Commission()

        self.monitor()

    def monitor(self):
        logger.debug('COMPS - Start Monitoring for experiment %s' % self.experiment.id)
        # Until done, update the status
        last_states = dict()
        for simulation in self.experiment.simulations:
            last_states[simulation.id] = simulation.status

        # Create the monitor
        monitor = CompsSimulationMonitor(self.experiment.exp_id, self.experiment.suite_id, self.experiment.endpoint)

        # Until done, update the status
        while True:
            logger.debug('COMPS - Waiting loop')
            try:
                states, _ = monitor.query()
            except Exception as e:
                logger.error('Exception in the COMPS Monitor for experiment %s' % self.experiment.id)
                logger.error(e)
                break

            diff_list = [key for key in set(last_states).intersection(states) if last_states[key] != states[key]]
            logger.debug('COMPS - Difflist for experiment %s' % self.experiment.id)
            logger.debug(diff_list)

            if len(diff_list) > 0:
                try:
                    self.lock.acquire()
                    for key in diff_list:
                        # Create the simulation to send to the update
                        self.states[key] = DataStore.create_simulation(status=states[key])

                        if states[key] == "Succeeded":
                            logger.debug("Simulation %s has succeeded, calling ths success callback" % key)
                            simulation = DataStore.get_simulation(key)
                            self.success(simulation)
                            logger.debug("Callback done for %s" % key)
                except Exception as e:
                    logger.error(e)
                finally:
                    self.lock.release()

                last_states = states

            if CompsExperimentManager.status_finished(states):
                logger.debug('Stop monitoring for experiment %s because all simulations finished' % self.experiment.id)
                break

            time.sleep(15)
