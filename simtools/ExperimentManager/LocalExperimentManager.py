import json
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
    monitorClass = SimulationMonitor
    parserClass = SimulationOutputParser

    def __init__(self, model_file, exp_data, setup=None):
        BaseExperimentManager.__init__(self, model_file, exp_data, setup)

        self.exp_builder = None
        self.staged_bin_path = None
        self.config_builder = None
        self.commandline = None
        self.analyzers = []

    def cancel_simulations(self, ids=[], killall=False):
        """
        Cancel currently some or all currently running simulations.

        Keyword arguments:
        ids -- a list of job ids to cancel
        killall -- a Boolean flag to kill all running simulations (default: False)
        """

        states, msgs = self.get_simulation_status()

        if killall:
            self.cancel_all_simulations(states)
            return

        for id in ids:
            if type(id) is str:
                id = int(id) if id.isdigit() else id  # arguments come in as strings (as they should for COMPS)

            state = states.get(id)
            if not state:
                logger.warning('No job in experiment with ID = %s' % id)
                continue

            if state not in ['Finished', 'Succeeded', 'Failed', 'Canceled', 'Unknown']:
                self.kill_job(id)
            else:
                logger.warning("JobID %s is already in a '%s' state." % (str(id), state))



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

    def resubmit_simulations(self, ids=[], resubmit_all_failed=False):
        """
        Resubmit some or all canceled or failed simulations.

        Keyword arguments:
        ids -- a list of job ids to resubmit
        resubmit_all_failed -- a Boolean flag to resubmit all canceled/failed simulations (default: False)
        """

        states, msgs = self.get_simulation_status()

        if resubmit_all_failed:
            ids = [id for (id, state) in states.iteritems() if state in ['Failed', 'Canceled']]
            logger.info('Resubmitting all failed simulations in experiment: ' + str(ids))

        for id in ids:
            state = states.get(id)
            if not state:
                logger.warning('No job in experiment with ID = %s' % id)
                continue

            if state in ['Failed', 'Canceled']:
                self.resubmit_job(id)
            else:
                logger.warning("JobID %d is in a '%s' state and will not be requeued." % (id, state))

    def analyze_simulations(self):
        """
        Apply one or more analyzers to the outputs of simulations.

        A parser thread will be spawned for each simulation with filtered analyzers to run,
        following which the combined outputs of all threads are reduced and displayed or saved.

        The analyzer interface provides the following methods:
           * filter -- based on the simulation meta-data return a Boolean to execute this analyzer
           * apply -- parse simulation output files and emit a subset of data
           * combine -- reduce the data emitted by each parser
           * finalize -- plotting and saving output files
        """

        parsers = {}

        for i, (sim_id, sim) in enumerate(self.exp_data['sims'].items()):

            filtered_analyses = [a for a in self.analyzers if a.filter(sim)]
            if not filtered_analyses:
                logger.debug('Simulation did not pass filter on any analyzer.')
                continue

            if self.maxThreadSemaphore:
                self.maxThreadSemaphore.acquire()
                logger.debug('Thread-%d: sim_id=%s', i, str(sim_id))

            parser = self.get_output_parser(sim_id, filtered_analyses)  # execute filtered analyzers on parser thread
            parser.start()
            parsers[parser.sim_id] = parser

        for p in parsers.values():
            p.join()

        if not parsers:
            logger.warn('No simulations passed analysis filters.')
            return

        for a in self.analyzers:
            a.combine(parsers)
            a.finalize()

    def create_suite(self, suite_name):
        suite_id = suite_name + '_' + re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating suite_id = " + suite_id)
        return suite_id

    def create_experiment(self, suite_id=None):
        exp_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.info("Creating exp_id = " + exp_id)
        sim_path = os.path.join(self.exp_data['sim_root'], self.exp_data['exp_name'] + '_' + exp_id)
        if not os.path.exists(sim_path):
            os.makedirs(sim_path)
        self.exp_data['sims'] = {}
        return exp_id

    def create_simulation(self):
        time.sleep(0.01)  # to avoid identical datetime
        sim_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.debug('Creating sim_id = ' + sim_id)
        sim_dir = os.path.join(self.exp_data['sim_root'], self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'],
                               sim_id)
        os.makedirs(sim_dir)
        self.config_builder.dump_files(sim_dir)
        self.exp_data['sims'][sim_id] = self.exp_builder.metadata

    def complete_sim_creation(self, commisioners=[]):
        return  # no batching in LOCAL

    def commission_simulations(self):
        # Retrieve the experiment dirs and the sim ids that we have to run
        exp_dir = os.path.join(self.exp_data['sim_root'], self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'])
        sim_ids = self.exp_data['sims'].keys()
        max_local_sims = int(self.get_property('max_local_sims'))

        # Create the paths
        paths = [os.path.join(exp_dir, sim_id) for sim_id in sim_ids]
        local_runner_path = os.path.join(os.path.dirname(os.path.realpath(__file__)),"..","SimulationRunner", "LocalRunner.py")
        cache_path = os.path.join(os.getcwd(), 'simulations',
                                  self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'] + '.json')

        # Open the local runner as a subprocess and pass it all the required info to run the simulations
        subprocess.Popen([sys.executable, local_runner_path, ",".join(paths),
                          self.commandline.Commandline, str(max_local_sims), cache_path], shell=False)

        super(LocalExperimentManager,self).commission_simulations()

        return True

    def cancel_all_simulations(self, states=None):

        if not states:
            states = self.get_simulation_status()[0]

        ids = states.keys()
        logger.info('Killing all simulations in experiment: ' + str(ids))
        self.cancel_simulations(ids)

    def kill_job(self, simId):
        pid = self.exp_data['sims'][simId]['pid'] if 'pid' in self.exp_data['sims'][simId] else None
        if pid:
            os.kill(pid, signal.SIGTERM)

    def resubmit_job(self, job_id):
        raise NotImplementedError('resubmit_job not implemented for %s jobs' % self.location)


    @staticmethod
    def status_succeeded(states):
        return all(v in ['Finished', 'Succeeded'] for v in states.itervalues())

    def succeeded(self):
        return self.status_succeeded(self.get_simulation_status()[0])

    @staticmethod
    def status_failed(states):
        return all(v in ['Failed'] for v in states.itervalues())

    def failed(self):
        return self.status_failed(self.get_simulation_status()[0])


    def get_output_parser(self, sim_id, filtered_analyses):
        return self.parserClass(os.path.join(self.exp_data.get('sim_root', ''),
                                             self.exp_data.get('exp_name', '') + '_' + self.exp_data.get('exp_id', '')),
                                sim_id,
                                self.exp_data['sims'][sim_id],
                                filtered_analyses,
                                self.maxThreadSemaphore)

    def add_analyzer(self, analyzer):
        self.analyzers.append(analyzer)


