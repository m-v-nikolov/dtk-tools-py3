import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.Monitor import SimulationMonitor
from simtools.OutputParser import SimulationOutputParser

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
        BaseExperimentManager.__init__(self, model_file, experiment, setup)

    def get_monitor(self):
        return SimulationMonitor(self.experiment.exp_id)

    def cancel_all_simulations(self, states=None):
        if not states:
            states = self.get_simulation_status()[0]

        ids = states.keys()
        logger.info('Killing all simulations in experiment: ')
        self.cancel_simulations(ids)

    def complete_sim_creation(self, commisioners=[]):
        return  # no batching in LOCAL

    def commission_simulations(self):
        # Prepare the info to pass to the localrunner
        max_local_sims = int(self.get_property('max_local_sims'))
        local_runner_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","SimulationRunner", "LocalRunner.py")

        # Open the local runner as a subprocess and pass it all the required info to run the simulations
        # The creationflags=512 asks Popen to create a new process group therefore not propagating the signals down
        # to the sub processes.
        subprocess.Popen([sys.executable, local_runner_path, str(max_local_sims), self.experiment.exp_id],
                         shell=False, creationflags=512)

        super(LocalExperimentManager,self).commission_simulations()

        return True

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

