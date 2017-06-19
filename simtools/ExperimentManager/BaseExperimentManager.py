from __future__ import print_function

from simtools.Utilities.General import init_logging, get_tools_revision
logger = init_logging('ExperimentManager')

import copy
import json
import multiprocessing
import os
import subprocess
import sys
import time
from abc import ABCMeta, abstractmethod
from collections import Counter

import dill
import fasteners

from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore, batch, dumper
from simtools.ModBuilder import SingleSimulationBuilder
from simtools.Monitor import SimulationMonitor
from simtools.OutputParser import SimulationOutputParser
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import validate_exp_name
from simtools.Utilities.General import is_running
from simtools.Utilities.LocalOS import LocalOS

current_dir = os.path.dirname(os.path.realpath(__file__))
from COMPS.Data.Simulation import SimulationState


class BaseExperimentManager:
    __metaclass__ = ABCMeta
    parserClass=SimulationOutputParser
    location = None

    def __init__(self, experiment, config_builder=None):
        self.experiment = experiment
        self.maxThreadSemaphore = multiprocessing.Semaphore(int(SetupParser.get('max_threads')))
        self.amanager = None
        self.exp_builder = None
        self._config_builder = None
        self.bypass_missing = False
        self.commandline = None
        self.experiment_tags = {}
        self.config_builder = config_builder

    @property
    def config_builder(self):
        return self._config_builder

    @config_builder.setter
    def config_builder(self, value):
        if not value or value == self._config_builder: return
        # Store the config builder
        self._config_builder = value
        # Get assets here for now
        self.assets = value.get_assets()
        # Check input files existence
        if not self.validate_input_files(): exit()
        # Set the appropriate command line
        self.commandline = self._get_commandline()

    @abstractmethod
    def commission_simulations(self, states):
        pass

    @staticmethod
    def create_suite(suite_name):
        pass

    @abstractmethod
    def kill_simulation(self, simulation):
        pass

    @abstractmethod
    def hard_delete(self):
        pass

    @abstractmethod
    def get_simulation_creator(self, function_set, max_sims_per_batch, callback, return_list, asset_cache):
        pass

    @abstractmethod
    def create_experiment(self, experiment_name, experiment_id, suite_id=None):
        self.experiment = DataStore.create_experiment(
            exp_id=experiment_id,
            suite_id=suite_id,
            sim_root=SetupParser.get('sim_root'),
            exp_name=experiment_name,
            location=self.location,
            analyzers=[],
            sim_type=self.config_builder.get_param('Simulation_Type'),
            dtk_tools_revision=get_tools_revision(),
            selected_block=SetupParser.selected_block,
            setup_overlay_file=SetupParser.overlay_path,
            working_directory=os.getcwd(),
            command_line=self.commandline.Commandline)

    def done_commissioning(self):
        self.experiment = DataStore.get_experiment(self.experiment.exp_id)
        for sim in self.experiment.simulations:
            if not sim.status or sim.status in [SimulationState.CommissionRequested, SimulationState.Created]:
                return False
        return True

    @staticmethod
    @fasteners.interprocess_locked(os.path.join(current_dir, '.overseer_check_lock'))
    def check_overseer():
        """
        Ensure that the overseer thread is running.
        The thread pid is retrieved from the settings and then we test if it corresponds to a python thread.
        If not, just start it.
        """
        logger.debug("Checking Overseer state")
        setting = DataStore.get_setting('overseer_pid')
        overseer_pid = int(setting.value) if setting else None

        # Launch the Overseer if needed
        if is_running(overseer_pid, name_part='python'):
            logger.debug("A valid Overseer was detected, pid: %d" % overseer_pid)
        else:
            logger.debug("A valid Overseer was not detected for stored pid %s." % overseer_pid)
            current_dir = os.path.dirname(os.path.realpath(__file__))
            runner_path = os.path.join(current_dir, '..', 'Overseer.py')
            if LocalOS.name in [LocalOS.WINDOWS, LocalOS.MAC]:
                p = subprocess.Popen([sys.executable, runner_path], shell=False, creationflags=512)
            else:
                p = subprocess.Popen([sys.executable, runner_path], shell=False)

            # Save the pid in the settings
            DataStore.save_setting(DataStore.create_setting(key='overseer_pid', value=str(p.pid)))

    def success_callback(self, simulation):
        """
        Called when the given simulation is done successfully
        """
        pass

    def get_simulation_status(self):
        """
        Query the status of simulations in the currently managed experiment.
        For example: SimulationState.Running,  .Succeeded, .Failed, .Canceled
        """
        self.check_overseer()
        states, msgs = SimulationMonitor(self.experiment.exp_id).query()
        return states, msgs

    def get_output_parser(self, simulation, filtered_analyses, semaphore, parse):
        return self.parserClass(simulation, filtered_analyses, semaphore, parse)

    def run_simulations(self, config_builder=None, exp_name='test', exp_builder=SingleSimulationBuilder(), suite_id=None,
                        analyzers=[], blocking=False, quiet=False, experiment_tags=None):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        Commission simulations and cache meta-data to local file.
        :assets: A SimulationAssets object if not None (COMPS-land needed for AssetManager)
        """
        # Check experiment name as early as possible
        if not validate_exp_name(exp_name):
            exit()

        # Store the config_builder if passed
        self.config_builder = config_builder or self.config_builder

        # Set the tags
        self.experiment_tags.update(experiment_tags or {})

        # Create the simulations
        self.create_simulations(exp_name=exp_name, exp_builder=exp_builder,
                                analyzers=analyzers, suite_id=suite_id, verbose=not quiet)

        # Make sure overseer is running
        self.check_overseer()

        if blocking:
            self.wait_for_finished(verbose=not quiet)

    def find_missing_files(self, input_files, input_root):
        """
        Find the missing files
        """
        missing_files = {}
        for (filename, filepath) in input_files.iteritems():
            if isinstance(filepath, basestring):
                filepath = filepath.strip()
                # Skip empty files
                if len(filepath) == 0:
                    continue
                # Only keep un-existing files
                if not os.path.exists(os.path.join(input_root, filepath)):
                    missing_files[filename] = filepath
            elif isinstance(filepath, list):
                # Skip empty and only keep un-existing files
                missing_files[filename] = [f.strip() for f in filepath if len(f.strip()) > 0
                                           and not os.path.exists(os.path.join(input_root, f.strip()))]
                # Remove empty list
                if len(missing_files[filename]) == 0:
                    missing_files.pop(filename)

        return missing_files

    def _detect_missing_files(self):
        missing_files = []
        for asset_type, asset in self.assets.collections.iteritems():
            for file in asset.asset_files_to_use:
                if file.is_local:
                    full_path = os.path.join(file.root, file.relative_path, file.file_name)
                    if not os.path.exists(full_path):
                        missing_files.append(full_path)
        return missing_files

    def validate_input_files(self):
        """
        Check input files and make sure they exist
        Note: we by pass the 'Campaign_Filename'
        This method only verifies local files, not (current) AssetManager-contained files
        """
        # By-pass input file checking if we want to bypass missing files
        if self.bypass_missing:
            return True

        # If the config builder has no file paths -> bypass
        if not hasattr(self.config_builder, 'get_input_file_paths'):
            return True

        missing_files = self._detect_missing_files()
        if len(missing_files) > 0:
            print('Missing files list:')
            print(json.dumps(missing_files, indent=2))
            var = raw_input("Above shows the missing input files, do you want to continue? [Y/N]:  ")
            if var.upper() == 'Y':
                print("Answer is '%s'. Continue..." % var.upper())
                return True
            else:
                print("Answer is '%s'. Exiting..." % var.upper())
                return False
        return True

    def create_simulations(self, exp_name='test', exp_builder=SingleSimulationBuilder(), analyzers=[],
                           suite_id=None, verbose=True):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        """
        self.exp_builder = exp_builder

        # Create the experiment if not present already
        if not self.experiment or self.experiment.exp_name != exp_name:
            self.create_experiment(experiment_name=exp_name, suite_id=suite_id)
        else:
            # Refresh the experiment
            self.experiment = DataStore.get_experiment(self.experiment.exp_id)

        # Add the analyzers
        for analyzer in analyzers:
            self.add_analyzer(analyzer)
            # Also add to the experiment
            self.experiment.analyzers.append(DataStore.create_analyzer(name=str(analyzer.__class__.__name__),
                                                                       analyzer=dill.dumps(analyzer)))

        # Save the experiment in the DB
        DataStore.save_experiment(self.experiment, verbose=verbose)

        # Separate the experiment builder generator into batches
        sim_per_batch = int(SetupParser.get('sims_per_thread', default=50))
        max_creator_processes = max(min(int(SetupParser.get('max_threads')), multiprocessing.cpu_count()-1),1)
        work_list = list(self.exp_builder.mod_generator)
        total_sims = len(work_list)

        # Batch the work to do differently depending on number of simulations
        if total_sims > sim_per_batch*max_creator_processes:
            nbatches = int(total_sims/max_creator_processes)
        else:
            nbatches = sim_per_batch
        fn_batches = batch(work_list, n=nbatches)

        # Create a manager for sharing the list of simulations created back with the main thread
        # Also create a dict for the cache of md5
        manager = multiprocessing.Manager()
        return_list = manager.list()
        asset_cache = manager.dict()

        # Create the simulation processes
        creator_processes = []
        for fn_batch in fn_batches:
            c = self.get_simulation_creator(function_set=fn_batch,
                                            max_sims_per_batch=sim_per_batch,
                                            callback=lambda: print('.' if verbose else '', end=""),
                                            return_list=return_list, asset_cache=asset_cache)
            creator_processes.append(c)

        # Display some info
        if verbose:
            logger.info("Creating the simulations (each . represent up to %s)" % sim_per_batch)
            logger.info(" | Creator processes: %s (max: %s)" % (len(creator_processes), max_creator_processes+1))
            logger.info(" | Simulations per batch: %s" % sim_per_batch)
            logger.info(" | Simulations Count: %s" % total_sims)
            logger.info(" | Max simulations per threads: %s" % nbatches)

        # Wait for all to finish
        map(lambda c: c.start(), creator_processes)
        map(lambda c: c.join(), creator_processes)

        # Insert all those newly created simulations to the DB
        DataStore.bulk_insert_simulations(return_list)

        # Refresh the experiment
        self.experiment = DataStore.get_experiment(self.experiment.exp_id)

        # Display sims
        if verbose:
            sims_to_display = 2
            display = -sims_to_display if total_sims > sims_to_display else -total_sims
            logger.info(" ")
            logger.info(json.dumps(self.experiment.simulations[display:], indent=3, default=dumper, sort_keys=True))
            if total_sims > sims_to_display: logger.info("... and %s more" % (total_sims + display))

    def refresh_experiment(self):
        # Refresh the experiment
        self.experiment = DataStore.get_experiment(self.experiment.exp_id)

    def print_status(self, states, msgs, verbose=True):
        long_states = copy.deepcopy(states)
        for jobid, state in states.items():
            long_states[jobid] = long_states[jobid].name
            if state is SimulationState.Running:
                steps_complete = [int(s) for s in msgs[jobid].split() if s.isdigit()]
                # convert the state value to a human-readable value
                if len(steps_complete) == 2:
                    long_states[jobid] += " (" + str(100 * steps_complete[0] / steps_complete[1]) + "% complete)"

        logger.info("%s ('%s') states:" % (self.experiment.exp_name, self.experiment.exp_id))
        if len(long_states) < 20 and verbose:
            # We have less than 20 simulations, display the simulations details
            logger.info(json.dumps(long_states, sort_keys=True, indent=4))
        # Display the counter no matter the number of simulations
        logger.info(dict(Counter( [st.name for st in states.values()] )))

    def delete_experiment(self, hard=False):
        """
        Delete experiment
        """
        if hard:
            self.hard_delete()
        else:
            self.soft_delete()

    def soft_delete(self):
        """
        Delete experiment in the DB
        """
        DataStore.delete_experiment(self.experiment)

    def wait_for_finished(self, verbose=False, sleep_time=5):
        # getch = helpers.find_getch()
        while True:
            # Get the new status
            try:
                states, msgs = self.get_simulation_status()
            except Exception as e:
                print("Exception occurred while retrieving status")
                print (e)
                return

            if self.status_finished(states):
                break
            else:
                if verbose:
                    self.print_status(states, msgs)

                # for i in range(sleep_time):
                #     if helpers.kbhit():
                #         if getch() == '\r':
                #             break
                #         else:
                #             return
                #     else:
                #         time.sleep(1)
                time.sleep(sleep_time)

        if verbose:
            self.print_status(states, msgs)

        # Refresh the experiment
        self.refresh_experiment()

    def analyze_experiment(self):
        """
        Deprecated: Use AnalyzeManager instead
        
        Apply one or more analyzers to the outputs of simulations.
        A parser thread will be spawned for each simulation with filtered analyzers to run,
        following which the combined outputs of all threads are reduced and displayed or saved.
        The analyzer interface provides the following methods:
           * filter -- based on the simulation meta-data return a Boolean to execute this analyzer
           * apply -- parse simulation output files and emit a subset of data
           * combine -- reduce the data emitted by each parser
           * finalize -- plotting and saving output files
        """
        self.amanager.analyze()

    def add_analyzer(self, analyzer, working_dir=None):
        logger.warning("The add_analyzer and analyze_experiment methods are deprecated. "
                       "The new way of analyzing an experiment is through AnalyzeManager. See examples/features/example_analyze.py for more information.")
        if not self.amanager: self.amanager = AnalyzeManager(self.experiment)
        self.amanager.add_analyzer(analyzer, working_dir)

    def kill(self, args, unknownArgs):
        if args.simIds:
            self.cancel_simulations([DataStore.get_simulation(id) for id in args.simIds])
        else:
            self.cancel_experiment()

    def cancel_experiment(self):
        logger.info("Cancelling experiment %s" % self.experiment.id)

    def cancel_simulations(self, sim_list):
        """
        Cancel all the simulations provided in id list.
        """
        sim_batch = []
        for simulation in sim_list:
            if simulation is None:
                continue

            if simulation.status not in [SimulationState.Succeeded, SimulationState.Failed,
                                         SimulationState.Canceled, SimulationState.CommissionRequested]:
                self.kill_simulation(simulation)

            # Add to the batch
            sim_batch.append({'sid':simulation.id, 'status':SimulationState.Canceled,'message':None, 'pid':None})

        # Batch update the statuses
        DataStore.batch_simulations_update(sim_batch)

    @staticmethod
    def status_succeeded(states):
        return all(v in [SimulationState.Succeeded] for v in states.itervalues())

    def succeeded(self):
        return self.status_succeeded(self.get_simulation_status()[0])

    @staticmethod
    def status_failed(states):
        return all(v in [SimulationState.Failed] for v in states.itervalues())

    @staticmethod
    def any_failed(states):
        return any(v in [SimulationState.Failed] for v in states.itervalues())

    @staticmethod
    def any_canceled(states):
        return any(v in [SimulationState.Canceled] for v in states.itervalues())

    def failed(self):
        return self.status_failed(self.get_simulation_status()[0])

    @staticmethod
    def status_finished(states):
        return all(v in [SimulationState.Succeeded, SimulationState.Failed, SimulationState.Canceled] for v in states.itervalues())

    def finished(self):
        return self.status_finished(self.get_simulation_status()[0])

    def _get_commandline(self):
        """
        Get the complete command line to run the simulations of this experiment.
        Returns:
            The :py:class:`CommandlineGenerator` object created with the correct paths

        """
        from simtools.Utilities.General import CommandlineGenerator

        eradication_options = {'--config': 'config.json'}

        python_path = SetupParser.get('python_path', default=None)
        if python_path:
            eradication_options['--python-script-path'] = python_path

        # ck4, not ideal, put in LocalExperimentManager?
        # If local, we need to potentially make a copy of the executable to a well-known place
        if self.location == 'LOCAL' and self.config_builder:
            exe_path = self.config_builder.stage_executable(self.assets.local_executable, SetupParser.get('bin_staging_root'))
            logger.debug("Staged LOCAL executable: %s to: %s" % (self.assets.local_executable, exe_path))
            eradication_options['--input-path'] = self.assets.local_input_root
        else:
            if self.location == 'LOCAL':
                return None
                #exe_path = None # os.path.join(SetupParser.get('sim_root'), 'Assets', os.path.basename(SetupParser.get('exe_path'))) # ck4, right?? Nope. Needs testing, if used at all.
                #eradication_options['--input-path'] = os.path.join(SetupParser.get('sim_root'), 'Assets') # ck4, right??? Nope. Needs testing, if used at all.
            elif self.location == 'HPC':
                exe_path = os.path.join('Assets', os.path.basename(SetupParser.get('exe_path')))
                eradication_options['--input-path'] = 'Assets'
            else:
                raise Exception("Unknown location: %s" % self.location)
        return CommandlineGenerator(exe_path, eradication_options, [])
