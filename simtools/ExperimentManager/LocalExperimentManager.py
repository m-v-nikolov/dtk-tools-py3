from simtools.SetupParser import SetupParser
from simtools.Utilities.General import init_logging
logger = init_logging("LocalExperimentManager")

import os
import re
import shutil
import signal
import threading
from datetime import datetime
from simtools.SetupParser import SetupParser
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.OutputParser import SimulationOutputParser
from simtools.SimulationCreator.LocalSimulationCreator import LocalSimulationCreator
from simtools.SimulationRunner.LocalRunner import LocalSimulationRunner
from simtools.Utilities.General import is_running

from COMPS.Data.Simulation import SimulationState

class LocalExperimentManager(BaseExperimentManager):
    """
    Manages the creation, submission, status, parsing, and analysis
    of local experiments, i.e. collections of related simulations
    """
    location = 'LOCAL'
    parserClass = SimulationOutputParser

    @property
    def experiment(self):
        return self._experiment

    @experiment.setter
    def experiment(self, experiment):
        """
        The experiment is a setter so we can refresh the unfinished simulations ids if new simulations are added
        """
        self._experiment = experiment
        if experiment:
            if hasattr(experiment, 'simulations'):
                for sim in experiment.simulations:
                    if sim.status not in [SimulationState.Failed, SimulationState.Succeeded, SimulationState.Canceled]:
                        if sim.id not in self.unfinished_simulations:
                            self.unfinished_simulations[sim.id] = sim

    def __init__(self, experiment, config_builder):
        self.local_queue = None
        self.simulations_commissioned = 0
        self.unfinished_simulations = {}
        self._experiment = None
        self.experiment = experiment

        BaseExperimentManager.__init__(self, experiment, config_builder)

    def commission_simulations(self, states):
        """
         Commissions all simulations that need to (and can be) commissioned.
        :param states: a multiprocessing.Queue for simulations to use to update their status.
        :return: The number of simulations commissioned.
        """
        to_commission = self.needs_commissioning()
        commissioned = []
        logger.debug("Commissioning up to %d simulation(s) (This many may need commissioning)." % len(to_commission))
        for simulation in to_commission:
            if self.local_queue.full():
                break
            else:
                logger.debug("Commissioning simulation: %s, its status was: %s" % (simulation.id, simulation.status.name))
                t1 = threading.Thread(target=LocalSimulationRunner,
                                      args=(simulation, self.experiment, self.local_queue, states, self.success_callback))
                t1.daemon = True
                t1.start()
                self.local_queue.put('run 1')
                commissioned.append(simulation)
        logger.debug("Commissioned %d simulation(s) (Limited by available thread count)." % len(commissioned))
        return len(commissioned)

    def needs_commissioning(self):
        """
        Determines which simulations need to be (re)started.
        :return: A list of Simulation objects
        """
        simulations = []
        # get the latest status information for all potentially unfinished simulations first
        if not len(self.unfinished_simulations) == 0:
            logger.debug("There are %d unfinished_simulation_ids to check." % len(self.unfinished_simulations))
            for sim in self.unfinished_simulations.values():
                if sim.status == SimulationState.Created or\
                        (sim.status == SimulationState.Running and not is_running(sim.pid, name_part='Eradication')):
                    logger.debug("Detected sim potentially in need of commissioning. sim id: %s sim status: %s sim pid: %s is_running? %s" %
                                 (sim.id, sim.status, sim.pid, is_running(sim.pid, name_part='Eradication')))
                    simulations.append(sim)
                elif sim.status in [SimulationState.Failed, SimulationState.Succeeded, SimulationState.Canceled]:
                    del self.unfinished_simulations[sim.id]
                    logger.debug("Choosing to NOT relaunch a sim: id: %s status: %s" % (sim.id, sim.status))
        return simulations

    def create_experiment(self, experiment_name, experiment_id=None, suite_id=None):
        experiment_name = self.clean_experiment_name(experiment_name)

        # Create a unique id
        experiment_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating exp_id = " + experiment_id)

        # Create the experiment in the base class
        super(LocalExperimentManager, self).create_experiment(experiment_name, experiment_id, suite_id)

        # Get the path and create it if needed
        experiment_path = self.experiment.get_path()
        if not os.path.exists(experiment_path):
            os.makedirs(experiment_path)

    @staticmethod
    def create_suite(suite_name):
        suite_id = suite_name + '_' + re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating suite_id = " + suite_id)
        return suite_id

    def hard_delete(self):
        """
        Delete experiment and output data.
        """
        # Perform soft delete cleanup.
        self.soft_delete()

        # Delete local simulation data.
        shutil.rmtree(self.experiment.get_path())

    def cancel_experiment(self):
        super(LocalExperimentManager, self).cancel_experiment()
        sim_list = [sim for sim in self.experiment.simulations if sim.status in [SimulationState.CommissionRequested, SimulationState.Running]]
        self.cancel_simulations(sim_list)

    def kill_simulation(self, simulation):
        # No need of trying to kill simulation already done
        if simulation.status in (SimulationState.Succeeded, SimulationState.Failed, SimulationState.Canceled):
            return

        # It was running -> Kill it if pid is there
        if simulation.pid:
            try:
                os.kill(int(simulation.pid), signal.SIGTERM)
            except Exception as e:
                print e

    def get_simulation_creator(self, function_set, max_sims_per_batch, callback, return_list):
        return LocalSimulationCreator(config_builder=self.config_builder,
                                      initial_tags=self.exp_builder.tags,
                                      function_set=function_set,
                                      max_sims_per_batch=max_sims_per_batch,
                                      experiment=self.experiment,
                                      callback=callback,
                                      return_list=return_list)
