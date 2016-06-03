import copy
import json
import logging
import os
import re
import signal
import subprocess
import threading
import time
import utils

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from collections import Counter
from SetupParser import SetupParser
from ModBuilder import SingleSimulationBuilder
from Commisioner import CompsSimulationCommissioner
from Monitor import SimulationMonitor, CompsSimulationMonitor
from OutputParser import SimulationOutputParser, CompsDTKOutputParser
from datetime import datetime

class ExperimentManagerFactory(object):
    @staticmethod
    def factory(type):
        if type == 'LOCAL':
            return LocalExperimentManager
        if type == 'HPC':
            return CompsExperimentManager
        raise Exception("ExperimentManagerFactory location argument should be either 'LOCAL' or 'HPC'.")

    @classmethod
    def from_model(cls, model_file, location='LOCAL'):
        logger.info('Initializing %s ExperimentManager from: %s', location, model_file)
        return cls.factory(location)(model_file, {})

    @classmethod
    def from_setup(cls, setup=SetupParser(), location='LOCAL', **kwargs):
        logger.info('Initializing %s ExperimentManager from parsed setup', location)
        if location == 'HPC' and kwargs:
            utils.override_HPC_settings(setup, **kwargs)
        return cls.factory(location)(setup.get('BINARIES', 'exe_path'), {}, setup)

    @classmethod
    def from_data(cls, exp_data):
        logger.info('Reloading ExperimentManager from experiment data')
        return cls.factory(exp_data['location'])('', exp_data)

    @classmethod
    def from_file(cls, exp_data_path, suppressLogging=False):
        if not suppressLogging:
            logger.info('Reloading ExperimentManager from: %s', exp_data_path)
        with open(exp_data_path) as exp_data_file:
            exp_data = json.loads(exp_data_file.read())
        return cls.factory(exp_data['location'])('', exp_data)


class LocalExperimentManager(object):
    """
    Manages the creation, submission, status, parsing, and analysis
    of local experiments, i.e. collections of related simulations
    """

    location = 'LOCAL'
    monitorClass = SimulationMonitor
    parserClass = SimulationOutputParser

    def __init__(self, model_file, exp_data, setup=SetupParser()):
        self.model_file = model_file
        self.exp_data = exp_data
        self.setup = setup

        self.exp_builder = None
        self.staged_bin_path = None
        self.config_builder = None
        self.commandline = None
        self.analyzers = []

        max_threads = int(self.setup.get('GLOBAL', 'max_threads'))
        self.maxThreadSemaphore = threading.Semaphore(max_threads)

    def create_simulations(self, config_builder, exp_name='test',
                           exp_builder=SingleSimulationBuilder(),
                           verbose=True, suite_id=None):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        """

        self.config_builder = config_builder
        self.exp_builder = exp_builder

        self.staged_bin_path = self.config_builder.stage_executable(self.model_file, self.get_setup())
        self.commandline = self.config_builder.get_commandline(self.staged_bin_path, self.get_setup())

        self.exp_data.update({'sim_root': self.get_property('sim_root'),
                              'exe_name': self.commandline.Executable,
                              'exp_name': exp_name,
                              'location': self.location,
                              'sim_type': self.config_builder.get_param('Simulation_Type')})

        self.exp_data['exp_id'] = self.create_experiment(suite_id)

        cached_cb = copy.deepcopy(self.config_builder)
        commissioners = []

        for mod_fn_list in self.exp_builder.mod_generator:
            # reset to base config/campaign
            self.config_builder = copy.deepcopy(cached_cb)

            # modify next simulation according to experiment builder
            map(lambda func: func(self.config_builder), mod_fn_list)

            # inside loop if different requirements by sim in sweep
            self.config_builder.stage_required_libraries(self.setup.get('BINARIES', 'dll_path'), self.get_setup())

            commissioner = self.create_simulation()
            if commissioner is not None:
                commissioners.append(commissioner)

        self.complete_sim_creation(commissioners)
        self.cache_experiment_data(verbose)

    def run_simulations(self, config_builder, exp_name='test',
                        exp_builder=SingleSimulationBuilder(),
                        suite_id=None):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        Commission simulations and cache meta-data to local file.
        """

        self.create_simulations(config_builder, exp_name, exp_builder, verbose=False, suite_id=suite_id)
        self.commission_simulations()
        self.cache_experiment_data()  # now we have job IDs

    def get_simulation_status(self, reload=False):
        """
        Query the status of simulations in the currently managed experiment.
        For example: 'Running', 'Finished', 'Succeeded', 'Failed', 'Canceled', 'Unknown'
        :param reload: Reload the exp_data (used in case of repeating poll with local simulations)
        """
        if reload:
            self.reload_exp_data()

        logger.debug("Status of simulations run on '%s':" % self.location)
        states, msgs = self.monitorClass(self.exp_data, self.get_setup()).query()
        return states, msgs

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
        paths = [os.path.join(exp_dir,sim_id) for sim_id in sim_ids]
        local_runner_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "LocalRunner.py")
        cache_path = os.path.join(os.getcwd(), 'simulations', self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'] + '.json')

        # Open the local runner as a subprocess and pass it all the required info to run the simulations
        subprocess.Popen(["python", local_runner_path, ",".join(paths),
                          self.commandline.Commandline, str(max_local_sims), cache_path], shell=False)

        return True

    def cancel_all_simulations(self, states=None):

        if not states:
            states = self.get_simulation_status()[0]

        ids = states.keys()
        logger.info('Killing all simulations in experiment: ' + str(ids))
        self.cancel_simulations(ids)

    def kill_job(self, job_id):
        os.kill(job_id, signal.SIGTERM)

    def resubmit_job(self, job_id):
        raise NotImplementedError('resubmit_job not implemented for %s jobs' % self.location)

    def get_property(self, property):
        return self.setup.get(self.location, property)

    def get_setup(self):
        return dict(self.setup.items(self.location))

    def cache_experiment_data(self, verbose=True):

        cache_path = os.path.join(os.getcwd(), 'simulations')

        if not os.path.exists(cache_path):
            os.mkdir(cache_path)

        with open(os.path.join(cache_path, self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'] + '.json'),
                  'w') as exp_file:
            if verbose:
                logger.info('Saving meta-data for experiment:')
                logger.info(json.dumps(self.exp_data, sort_keys=True, indent=4))
            exp_file.write(json.dumps(self.exp_data, sort_keys=True, indent=4))

    @staticmethod
    def print_status(states, msgs):
        long_states = copy.deepcopy(states)
        for jobid, state in states.items():
            if 'Running' in state:
                steps_complete = [int(s) for s in msgs[jobid].split() if s.isdigit()]
                if len(steps_complete) == 2:
                    long_states[jobid] += " (" + str(100 * steps_complete[0] / steps_complete[1]) + "% complete)"

        logger.info('Job states:')
        if len(long_states) < 20:
            # We have less than 20 simulations, display the simulations details
            logger.info(json.dumps(long_states, sort_keys=True, indent=4))
        # Display the counter no matter the number of simulations
        logger.info(dict(Counter(states.values())))

    @staticmethod
    def status_finished(states):
        return all(v in ['Finished', 'Succeeded', 'Failed', 'Canceled'] for v in states.itervalues())

    def finished(self):
        return self.status_finished(self.get_simulation_status()[0])

    @staticmethod
    def status_succeeded(states):
        return all(v in ['Finished', 'Succeeded'] for v in states.itervalues())

    def succeeded(self):
        return self.status_succeeded(self.get_simulation_status()[0])

    def wait_for_finished(self, verbose=False, init_sleep=0.1, sleep_time=3):
        while True:
            time.sleep(init_sleep)

            # Reload the exp_data because job ids may have been added by the thread
            self.reload_exp_data()

            states, msgs = self.get_simulation_status()
            if self.status_finished(states):
                break
            else:
                if verbose:
                    self.print_status(states, msgs)
                time.sleep(sleep_time)
        self.print_status(states, msgs)

    def get_output_parser(self, sim_id, filtered_analyses):
        return self.parserClass(os.path.join(self.exp_data.get('sim_root', ''),
                                             self.exp_data.get('exp_name', '') + '_' + self.exp_data.get('exp_id', '')),
                                sim_id,
                                self.exp_data['sims'][sim_id],
                                filtered_analyses,
                                self.maxThreadSemaphore)

    def add_analyzer(self, analyzer):
        self.analyzers.append(analyzer)

    def reload_exp_data(self):
        """
        Refresh the exp_data with what is in the json metadata
        :return:
        """
        cache_file_path = os.path.join(os.getcwd(), 'simulations',
                                       "%s_%s.json" % (self.exp_data['exp_name'], self.exp_data['exp_id']))
        self.exp_data = json.load(open(cache_file_path))


class CompsExperimentManager(LocalExperimentManager):
    """
    Extends the LocalExperimentManager to manage DTK simulations through COMPS wrappers
    e.g. creation of Simulation, Experiment, Suite objects
    """

    location = 'HPC'
    monitorClass = CompsSimulationMonitor
    parserClass = CompsDTKOutputParser

    def __init__(self, exe_path, exp_data, setup=SetupParser()):
        LocalExperimentManager.__init__(self, exe_path, exp_data, setup)
        self.comps_logged_in = False
        self.comps_sims_to_batch = int(self.get_property('sims_per_thread'))
        self.commissioner = None
        self.sims_created = 0

    def create_suite(self, suite_name):
        return CompsSimulationCommissioner.create_suite(self.setup, suite_name)

    def create_experiment(self, suite_id=None):
        self.sims_created = 0
        return CompsSimulationCommissioner.create_experiment(self.setup, self.config_builder,
                                                             self.exp_data['exp_name'], self.staged_bin_path,
                                                             self.commandline.Options, suite_id)

    def create_simulation(self):
        if self.sims_created % self.comps_sims_to_batch == 0:
            self.maxThreadSemaphore.acquire()  # Is this okay outside the thread?  Stops the thread from being created
            # until it can actually go, but asymmetrical acquire()/release() is not
            # ideal...

            self.commissioner = CompsSimulationCommissioner(self.exp_data['exp_id'], self.maxThreadSemaphore)
            ret = self.commissioner
        else:
            ret = None

        files = self.config_builder.dump_files_to_string()
        tags = self.exp_builder.metadata
        self.commissioner.create_simulation(self.config_builder.get_param('Config_Name'), files, tags)

        self.sims_created += 1

        if self.sims_created % self.comps_sims_to_batch == 0:
            self.commissioner.start()
            self.commissioner = None

        return ret

    def complete_sim_creation(self, commissioners):
        lastBatch = commissioners[-1]
        if not lastBatch.isAlive() and len(lastBatch.sims) > 0:
            lastBatch.start()
        for c in commissioners:
            c.join()
        self.collect_sim_metadata()

    def commission_simulations(self):
        CompsSimulationCommissioner.commission_experiment(self.exp_data['exp_id'])
        return True

    def collect_sim_metadata(self):
        self.exp_data['sims'] = CompsSimulationCommissioner.get_sim_metadata_for_exp(self.exp_data['exp_id'])

    def cancel_all_simulations(self, states=None):
        from COMPS import Client
        from COMPS.Data import Experiment, QueryCriteria

        Client.Login(self.get_property('server_endpoint'))

        e = Experiment.GetById(self.exp_data['exp_id'], QueryCriteria().Select('Id'))
        e.Cancel()

    def kill_job(self, job_id):
        from COMPS import Client
        from COMPS.Data import Simulation, QueryCriteria

        if not self.comps_logged_in:
            Client.Login(self.get_property('server_endpoint'))
            self.comps_logged_in = True

        s = Simulation.GetById(job_id, QueryCriteria().Select('Id'))
        s.Cancel()

    def analyze_simulations(self):
        if not self.setup.getboolean(self.location, 'use_comps_asset_svc'):
            CompsDTKOutputParser.createSimDirectoryMap(self.exp_data.get('exp_id'), self.exp_data.get('suite_id'))
        if self.setup.getboolean(self.location, 'compress_assets'):
            CompsDTKOutputParser.enableCompression()

        LocalExperimentManager.analyze_simulations(self)
