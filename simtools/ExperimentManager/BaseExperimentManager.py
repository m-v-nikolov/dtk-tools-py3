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

import fasteners

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

def print_status_func():
    print(".", end="")

class BaseExperimentManager:
    __metaclass__ = ABCMeta
    parserClass=SimulationOutputParser
    location = None

    def __init__(self, experiment, config_builder=None):
        self.experiment = experiment
        self.exp_builder = None
        self.config_builder = config_builder
        self.commandline = None
        self.experiment_tags = {}
        self.asset_service = None
        self.assets = None

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
    def get_simulation_creator(self, function_set, max_sims_per_batch, callback, return_list):
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
            runner_path = os.path.abspath(os.path.join(current_dir, '..', 'Overseer.py'))
            if LocalOS.name in (LocalOS.WINDOWS, LocalOS.MAC):
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
                        blocking=False, quiet=False, experiment_tags=None):
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

        # Get the assets from the config builder
        # We just want to check the input files at this point even though it may change later
        self.assets = self.config_builder.get_assets()

        # Check input files existence
        if not self.config_builder.ignore_missing and not self.validate_input_files(): exit()

        # Set the appropriate command line
        self.commandline = self.config_builder.get_commandline()

        # Set the tags
        self.experiment_tags.update(experiment_tags or {})

        # Create the simulations
        self.create_simulations(exp_name=exp_name, exp_builder=exp_builder, suite_id=suite_id, verbose=not quiet)

        # Make sure overseer is running
        self.check_overseer()

        if blocking:
            self.wait_for_finished(verbose=not quiet)

    def validate_input_files(self):
        """
        Check input files and make sure they exist
        Note: we by pass the 'Campaign_Filename'
        This method only verifies local files, not (current) AssetManager-contained files
        """
        # Get the needed file paths
        needed_file_paths = self.config_builder.get_input_file_paths()

        missing_files = []
        for needed_file in needed_file_paths:
            if os.path.basename(needed_file) not in self.assets:
                missing_files.append(needed_file)

        if len(missing_files) > 0:
            print('The following files are specified in the config.json file but not present in the available assets:')
            map(lambda f: print("- %s" % f), missing_files)

            var = input("The simulation may not run, do you want to continue? [Y/N]:  ")
            if var.upper() == 'Y':
                print("Answer is '%s'. Continue..." % var.upper())
                return True
            else:
                print("Answer is '%s'. Exiting..." % var.upper())
                return False
        return True

    def create_simulations(self, exp_name='test', exp_builder=SingleSimulationBuilder(), suite_id=None, verbose=True):
        """
        Create an experiment with simulations modified according to the specified experiment builder.
        """
        self.exp_builder = exp_builder

        # Create the experiment if not present already
        if not self.experiment or self.experiment.exp_name != exp_name:
            self.create_experiment(experiment_name=exp_name, suite_id=suite_id)
        else:
            # Refresh the experiment
            self.refresh_experiment()

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

        if verbose:
            callback = print_status_func
        else:
            callback = None

        # Create the simulation processes
        creator_processes = []
        for fn_batch in fn_batches:
            c = self.get_simulation_creator(function_set=fn_batch,
                                            max_sims_per_batch=sim_per_batch,
                                            callback=callback,
                                            return_list=return_list)
            creator_processes.append(c)

        # Display some info
        if verbose:
            logger.info("Creating the simulations (each . represent up to %s)" % sim_per_batch)
            logger.info(" | Creator processes: %s (max: %s)" % (len(creator_processes), max_creator_processes+1))
            logger.info(" | Simulations per batch: %s" % sim_per_batch)
            logger.info(" | Simulations Count: %s" % total_sims)
            logger.info(" | Max simulations per threads: %s" % nbatches)

        # Wait for all to finish
        for c in creator_processes:
            c.start()

        for c in creator_processes:
            c.join()

        # Insert all those newly created simulations to the DB
        DataStore.bulk_insert_simulations(return_list)

        # Refresh the experiment
        self.refresh_experiment()

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

    def print_status(self, states=None, msgs=None, verbose=True):
        if not states:
            states, msgs = self.get_simulation_status()

        long_states = copy.deepcopy(states)

        for jobid, state in states.items():
            long_states[jobid] = long_states[jobid].name
            if state is SimulationState.Running:
                steps_complete = [int(s) for s in msgs[jobid].split() if s.isdigit()]
                # convert the state value to a human-readable value
                if len(steps_complete) == 2:
                    # long_states[jobid] += " (" + str(100 * steps_complete[0] / steps_complete[1]) + "% complete)"
                    long_states[jobid] += " (" + "{0:.2f}".format(
                        100 * steps_complete[0] / steps_complete[1]) + "% complete)"

        print("%s ('%s') states:" % (self.experiment.exp_name, self.experiment.exp_id))

        # We have less than 20 simulations, display the simulations details
        if len(long_states) < 20 and verbose:
            print(json.dumps(long_states, sort_keys=True, indent=4))

        # Display the counter no matter the number of simulations
        print(dict(Counter([st.name for st in states.values()])))

    def delete_experiment(self):
        # Delete on COMPS/local files
        self.hard_delete()

        # Delete in the DB
        DataStore.delete_experiment(self.experiment)

    def wait_for_finished(self, verbose=False, sleep_time=5):
        timeout = 3600 * 24 # 48 hours timeout
        while True:
            # Get the new status
            try:
                states, msgs = self.get_simulation_status()
            except Exception as e:
                print("Exception occurred while retrieving status")
                print(e)
                return

            if timeout < 0:
                raise Exception("Timeout exhausted for experiment {}".format(self.experiment.exp_id))

            # If we are done, exit the loop
            if self.status_finished(states): break

            # Display if verbose
            if verbose:
                self.print_status(states, msgs)
                print("")

            # Wait before going through the loop again
            time.sleep(sleep_time)
            timeout -= sleep_time

        # SHow status one last time
        if verbose: self.print_status(states, msgs)

        # Refresh the experiment
        self.refresh_experiment()

    def kill(self, sim_ids=None):
        if sim_ids:
            self.cancel_simulations([DataStore.get_simulation(id) for id in sim_ids])
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
        return all(v in [SimulationState.Succeeded] for v in states.values())

    def succeeded(self):
        return self.experiment.is_successful()

    @staticmethod
    def status_failed(states):
        return all(v in [SimulationState.Failed] for v in states.values())

    def any_failed_or_cancelled(self):
        return self.experiment.any_failed_or_cancelled()

    @staticmethod
    def status_finished(states):
        return all(v in [SimulationState.Succeeded, SimulationState.Failed, SimulationState.Canceled] for v in states.values())

    def finished(self):
        return self.experiment.is_done()

    def clean_experiment_name(self, experiment_name):
        """
        Enforce any COMPS-specific demands on experiment names.
        :param experiment_name: a str
        :return: the experiment name allowed for use (e.g. may be cleaned)
        """
        # cleaning step
        for c in ['/', '\\', ':']:
            experiment_name = experiment_name.replace(c, '_')
        return experiment_name

