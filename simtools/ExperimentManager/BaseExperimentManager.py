import copy
import json
import logging
import os
import threading
from abc import ABCMeta, abstractmethod
from collections import Counter

import time

from simtools import utils
from simtools.ModBuilder import SingleSimulationBuilder
from simtools.SetupParser import SetupParser


logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class BaseExperimentManager:
    __metaclass__ = ABCMeta

    def __init__(self, model_file, exp_data, setup=None):
        # If no setup is passed -> create it
        if setup is None:
            selected_block = exp_data['selected_block'] if 'selected_block' in exp_data else 'LOCAL'
            setup_file = exp_data['setup_overlay_file'] if 'setup_overlay_file' in exp_data else None
            self.setup = SetupParser(selected_block=selected_block, setup_file=setup_file, fallback='LOCAL')
        else:
            self.setup = setup

        self.model_file = model_file
        self.exp_data = exp_data
        max_threads = int(self.setup.get('max_threads'))
        self.maxThreadSemaphore = threading.Semaphore(max_threads)
        self.assets_service = False
        self.quiet = self.setup.has_option('quiet')
        self.blocking = self.setup.has_option('blocking')
        self.analyzers = []
        self.exp_builder = None
        self.staged_bin_path = None
        self.config_builder = None
        self.commandline = None
        self.location = self.setup.get('type')


    @abstractmethod
    def cancel_all_simulations(self, states=None):
        pass

    @abstractmethod
    def commission_simulations(self):
        if self.blocking:
            self.wait_for_finished(verbose=not self.quiet)

    @abstractmethod
    def create_experiment(self, suite_id=None):
        pass

    @abstractmethod
    def create_simulation(self, suite_id=None):
        pass

    @abstractmethod
    def create_suite(self, suite_name):
        pass

    @abstractmethod
    def complete_sim_creation(self,commissioners):
        pass

    @abstractmethod
    def kill_job(self, simId):
        pass

    @abstractmethod
    def hard_delete(self):
        pass

    def get_property(self, prop):
        return self.setup.get(prop)

    def get_setup(self):
        return dict(self.setup.items())

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

    def get_output_parser(self, sim_id, filtered_analyses):
        return self.parserClass(os.path.join(self.exp_data.get('sim_root', ''),
                                             self.exp_data.get('exp_name', '') + '_' + self.exp_data.get('exp_id', '')),
                                sim_id,
                                self.exp_data['sims'][sim_id],
                                filtered_analyses,
                                self.maxThreadSemaphore)

    def run_simulations(self, config_builder, exp_name='test', exp_builder=SingleSimulationBuilder(), suite_id=None):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        Commission simulations and cache meta-data to local file.
        """
        self.create_simulations(config_builder, exp_name, exp_builder, suite_id=suite_id, verbose=not self.quiet)
        self.commission_simulations()
        self.cache_experiment_data(verbose=False)  # now we have job IDs

    def create_simulations(self, config_builder, exp_name='test', exp_builder=SingleSimulationBuilder(), suite_id=None, verbose=True):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        """
        self.config_builder = config_builder
        self.exp_builder = exp_builder

        # If the assets service is in use, do not stage the exe and just return whats in tbe bin_staging_path
        # If not, use the normal staging process
        if self.assets_service:
            self.staged_bin_path = self.setup.get('bin_staging_root')
        else:
            self.staged_bin_path = self.config_builder.stage_executable(self.model_file, self.get_setup())

        # Create the command line
        self.commandline = self.config_builder.get_commandline(self.staged_bin_path, self.get_setup())

        # Set the meta data
        self.exp_data.update({'sim_root': self.get_property('sim_root'),
                              'exe_name': self.commandline.Executable,
                              'exp_name': exp_name,
                              'location': self.location,
                              'sim_type': self.config_builder.get_param('Simulation_Type'),
                              'dtk-tools_revision': utils.get_tools_revision(),
                              'selected_block': self.setup.selected_block,
                              'setup_overlay_file': self.setup.setup_file})

        self.exp_data['exp_id'] = self.create_experiment(suite_id)

        cached_cb = copy.deepcopy(self.config_builder)
        commissioners = []

        for mod_fn_list in self.exp_builder.mod_generator:
            # reset to base config/campaign
            self.config_builder = copy.deepcopy(cached_cb)

            # modify next simulation according to experiment builder
            map(lambda func: func(self.config_builder), mod_fn_list)

            # If the assets service is in use, the path needs to come from COMPS
            if self.assets_service:
                lib_staging_root = utils.translate_COMPS_path(self.setup.get('lib_staging_root'), self.setup)
            else:
                lib_staging_root = self.setup.get('lib_staging_root')

            # Stage the required dll for the experiment
            self.config_builder.stage_required_libraries(self.setup.get('dll_path'), lib_staging_root,
                                                         self.assets_service)

            commissioner = self.create_simulation()
            if commissioner is not None:
                commissioners.append(commissioner)

        self.complete_sim_creation(commissioners)
        self.cache_experiment_data(verbose=verbose)

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

    def reload_exp_data(self):
        """
        Refresh the exp_data with what is in the json metadata
        :return:
        """
        cache_file_path = os.path.join(os.getcwd(), 'simulations', "%s_%s.json" % (self.exp_data['exp_name'], self.exp_data['exp_id']))

        try:
            self.exp_data = json.load(open(cache_file_path))
        except:
            logger.info('Experiment data file locked.')

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

    def print_status(self,states, msgs):
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

    def soft_delete(self):
        """
        Delete local cache data for experiment.
        """
        # First, ensure that all simulations are canceled.
        states, msgs = self.get_simulation_status()
        self.cancel_all_simulations(states)

        # Wait for successful cancellation.
        self.wait_for_finished(verbose=True)

        # Delete local cache file.
        cache_file = os.path.join(os.getcwd(), 'simulations',
                                  self.exp_data['exp_name'] + '_' + self.exp_data['exp_id'] + '.json')
        os.remove(cache_file)

    def wait_for_finished(self, verbose=False, init_sleep=0.1, sleep_time=3):
        while True:
            time.sleep(init_sleep)

            # Reload the exp_data because job ids may have been added by the thread
            states, msgs = self.get_simulation_status(reload=True)
            if self.status_finished(states):
                # Wait when we are all done to make sure all the output files have time to get written
                time.sleep(sleep_time)
                break
            else:
                if verbose:
                    self.print_status(states, msgs)
                time.sleep(sleep_time)

        if verbose:
            self.print_status(states, msgs)

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

    def add_analyzer(self, analyzer):
        self.analyzers.append(analyzer)

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

    @staticmethod
    def status_succeeded(states):
        return all(v in ['Finished', 'Succeeded'] for v in states.itervalues())

    def succeeded(self):
        return self.status_succeeded(self.get_simulation_status()[0])

    @staticmethod
    def status_failed(states):
        return all(v in ['Failed'] for v in states.itervalues())

    @staticmethod
    def any_failed(states):
        return any(v in ['Failed'] for v in states.itervalues())

    @staticmethod
    def any_canceled(states):
        return any(v in ['Canceled'] for v in states.itervalues())

    def failed(self):
        return self.status_failed(self.get_simulation_status()[0])

    @staticmethod
    def status_finished(states):
        return all(v in ['Finished', 'Succeeded', 'Failed', 'Canceled'] for v in states.itervalues())

    def finished(self):
        return self.status_finished(self.get_simulation_status()[0])