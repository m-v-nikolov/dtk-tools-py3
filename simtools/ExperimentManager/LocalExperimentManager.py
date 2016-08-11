import logging
import os
import re
import shutil
import signal
import subprocess
import sys
import time
from datetime import datetime

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

    def __init__(self, model_file, exp_data, setup=None):
        BaseExperimentManager.__init__(self, model_file, exp_data, setup)

    def get_monitor(self):
        return SimulationMonitor(self.exp_data)

    def cancel_all_simulations(self, states=None):

        if not states:
            states = self.get_simulation_status()[0]

        ids = states.keys()
        logger.info('Killing all simulations in experiment: ' + str(ids))
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
        subprocess.Popen([sys.executable, local_runner_path, str(max_local_sims), self.exp_data['exp_id']], shell=False, creationflags=512)

        super(LocalExperimentManager,self).commission_simulations()

        return True

    def create_experiment(self, suite_id=None):
        exp_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating exp_id = " + exp_id)
        sim_path = os.path.join(self.exp_data['sim_root'], self.exp_data['exp_name'] + '_' + exp_id)
        if not os.path.exists(sim_path):
            os.makedirs(sim_path)
        self.exp_data['simulations'] = []
        return exp_id

    def create_simulation(self):
        time.sleep(0.01)  # to avoid identical datetime
        sim_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.debug('Creating sim_id = ' + sim_id)
        sim_dir = os.path.join(self.exp_data['sim_root'], self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'],
                               sim_id)
        os.makedirs(sim_dir)
        self.config_builder.dump_files(sim_dir)
        self.exp_data['simulations'].append(self.data_store.create_simulation(id=sim_id, tags=self.exp_builder.metadata))

    def create_suite(self, suite_name):
        suite_id = suite_name + '_' + re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating suite_id = " + suite_id)
        return suite_id

    def hard_delete(self):
        """
        Delete local cache data for experiment and output data for experiment.
        """
        # Perform soft delete cleanup.
        self.soft_delete()

        # Delete local simulation data.
        local_data_path = os.path.join(self.exp_data['sim_root'],
                                       self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'])
        shutil.rmtree(local_data_path)

    def kill_job(self, simId):
        # if the status has not been set -> set it to Canceled
        if 'status' not in self.exp_data['sims'][simId]:
            self.exp_data['sims'][simId]['status'] = 'Canceled'
            self.cache_experiment_data(verbose=False)
            return

        # No need of trying to kill simulation already done
        if self.exp_data['sims'][simId]['status'] in ('Finished', 'Succeeded', 'Failed', 'Canceled'):
            return

        pid = self.exp_data['sims'][simId]['pid'] if 'pid' in self.exp_data['sims'][simId] else None
        if pid:
            try:
                self.exp_data['sims'][simId]['status'] = 'Canceled'
                self.cache_experiment_data(verbose=False)
                os.kill(pid, signal.SIGTERM)
            except:
                pass

