import os
import re
import shutil
import signal
import threading
from datetime import datetime

from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.OutputParser import SimulationOutputParser
from simtools.SimulationCreator.LocalSimulationCreator import LocalSimulationCreator
from simtools.SimulationRunner.LocalRunner import LocalSimulationRunner
from simtools.utils import init_logging

logger = init_logging("ExperimentManager")


class LocalExperimentManager(BaseExperimentManager):
    """
    Manages the creation, submission, status, parsing, and analysis
    of local experiments, i.e. collections of related simulations
    """
    location = 'LOCAL'
    parserClass = SimulationOutputParser
    creatorClass = LocalSimulationCreator

    def __init__(self, model_file, experiment, setup=None):
        self.local_queue = None
        self.simulations_commissioned = 0
        BaseExperimentManager.__init__(self, model_file, experiment, setup)

    def commission_simulations(self, states):
        if not self.local_queue:
            from Queue import Queue
            self.local_queue = Queue()
        while not self.local_queue.full() and self.simulations_commissioned < len(self.experiment.simulations):
            simulation = self.experiment.simulations[self.simulations_commissioned]
            # If the simulation is not waiting, we can go to the next one
            # Useful if the simulation is cancelled before being commission
            if simulation.status != "Waiting":
                self.simulations_commissioned += 1
                continue
            self.local_queue.put('run 1')
            t1 = threading.Thread(target=LocalSimulationRunner, args=(simulation, self.experiment, self.local_queue, states, self.success_callback))
            t1.daemon = True
            t1.start()
            self.simulations_commissioned += 1

        if self.simulations_commissioned == len(self.experiment.simulations):
            self.runner_created = True

    def check_input_files(self, input_files):
        """
        Check file exist and return the missing files as dict
        """
        input_root = self.setup.get('input_root')
        return input_root, self.find_missing_files(input_files, input_root)

    def create_experiment(self, experiment_name, experiment_id=re.sub('[ :.-]', '_', str(datetime.now())),suite_id=None):
        logger.info("Creating exp_id = " + experiment_id)

        # Create the experiment in the base class
        super(LocalExperimentManager,self).create_experiment(experiment_name, experiment_id, suite_id)

        # Get the path and create it if needed
        experiment_path = self.experiment.get_path()
        if not os.path.exists(experiment_path):
            os.makedirs(experiment_path)

    def create_suite(self, suite_name):
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
        sim_list = [sim for sim in self.experiment.simulations if sim.status in ["Waiting","Running"]]
        self.cancel_simulations(sim_list)

    def kill_simulation(self, simulation):
        # No need of trying to kill simulation already done
        if simulation.status in ('Succeeded', 'Failed', 'Canceled'):
            return

        # It was running -> Kill it if pid is there
        if simulation.pid:
            try:
                os.kill(int(simulation.pid), signal.SIGTERM)
            except Exception as e:
                print e
