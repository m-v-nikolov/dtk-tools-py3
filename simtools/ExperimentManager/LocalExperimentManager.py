import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from datetime import datetime
import platform

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.Monitor import SimulationMonitor
from simtools.OutputParser import SimulationOutputParser
from simtools.SimulationRunner.LocalRunner import LocalSimulationCommissioner

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class LocalExperimentManager(BaseExperimentManager):
    """
    Manages the creation, submission, status, parsing, and analysis
    of local experiments, i.e. collections of related simulations
    """

    location = 'LOCAL'
    parserClass = SimulationOutputParser

    def __init__(self, model_file, experiment, setup=None):
        self.local_queue = None
        self.simulations_commissioned = 0
        BaseExperimentManager.__init__(self, model_file, experiment, setup)

    def get_parser(self, experiment_path, simulation_id, simulation_tags, filtered_analysis, semaphore):
        return SimulationOutputParser(experiment_path, simulation_id, simulation_tags, filtered_analysis, semaphore)

    def commission_simulations(self, states):
        while not self.local_queue.full() and self.simulations_commissioned < len(self.experiment.simulations):
            self.local_queue.put('run 1')
            simulation = self.experiment.simulations[self.simulations_commissioned]
            t1 = threading.Thread(target=LocalSimulationCommissioner, args=(simulation, self.experiment, self.local_queue, states, self.success_callback))
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

        missing_files = {}
        for (filename, filepath) in input_files.iteritems():
            if isinstance(filepath, basestring):
                if not os.path.exists(os.path.join(input_root, filepath)):
                    missing_files[filename] = filepath
            elif isinstance(filepath, list):
                missing_files[filename] = [f for f in filepath if not os.path.exists(os.path.join(input_root, f))]
                # Remove empty list
                if len(missing_files[filename]) == 0:
                    missing_files.pop(filename)

        return missing_files

    def cancel_all_simulations(self, states=None):
        if not states:
            states = self.get_simulation_status()[0]

        ids = states.keys()
        logger.info('Killing all simulations in experiment: ')
        self.cancel_simulations(ids)

    def complete_sim_creation(self, commisioners=[]):
        return  # no batching in LOCAL

    def create_experiment(self, experiment_name, suite_id=None):
        # Create a unique id
        exp_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating exp_id = " + exp_id)

        # Create the experiment in the base class
        super(LocalExperimentManager,self).create_experiment(experiment_name, exp_id, suite_id)

        # Get the path and create it if needed
        experiment_path = self.experiment.get_path()
        if not os.path.exists(experiment_path):
            os.makedirs(experiment_path)

    def create_simulation(self):
        time.sleep(0.01)  # to avoid identical datetime
        sim_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.debug('Creating sim_id = ' + sim_id)
        sim_dir = os.path.join(self.experiment.get_path(), sim_id)
        os.makedirs(sim_dir)
        self.config_builder.dump_files(sim_dir)
        self.experiment.simulations.append(DataStore.create_simulation(id=sim_id, tags=self.exp_builder.metadata, status='Waiting'))

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

    def kill_job(self, simId):

        simulation = DataStore.get_simulation(simId)

        # No need of trying to kill simulation already done
        if simulation.status in ('Succeeded', 'Failed', 'Canceled'):
            return

        # if the status has not been set -> set it to Canceled
        if not simulation.status or simulation.status == 'Waiting':
            simulation.status = 'Canceled'
            DataStore.save_simulation(simulation)
            return

        # It was running -> Kill it if pid is there
        if simulation.pid:
            try:
                simulation.status = 'Canceled'
                DataStore.save_simulation(simulation)
                os.kill(int(simulation.pid), signal.SIGTERM)
            except Exception as e:
                print e

