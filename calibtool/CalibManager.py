import gc
import glob
import json
import logging
import os
import pprint
import re
import shutil
import time
from datetime import datetime

import pandas as pd

from IterationState import IterationState
from calibtool.plotters import SiteDataPlotter
from calibtool.utils import ResumePoint
from core.utils.time import verbose_timedelta
from simtools import utils
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.utils import NumpyEncoder

logger = logging.getLogger("Calibration")


class SampleIndexWrapper(object):
    """
    Wrapper for a SimConfigBuilder-modifying function to add metadata
    on sample-point index when called in a iteration over sample points
    """

    def __init__(self, map_sample_to_model_input_fn):
        self.map_sample_to_model_input_fn = map_sample_to_model_input_fn

    def __call__(self, idx):
        def func(cb, *args, **kwargs):
            params_dict = self.map_sample_to_model_input_fn(cb, *args, **kwargs)
            params_dict.update(cb.set_param('__sample_index__', idx))
            return params_dict

        return func


class CalibManager(object):
    """
    Manages the creation, execution, and resumption of multi-iteration a calibration suite.
    Each iteration spawns a new ExperimentManager to configure and commission either local
    or HPC simulations for a set of random seeds, sample points, and site configurations.
    """

    def __init__(self, setup, config_builder, map_sample_to_model_input_fn,
                 sites, next_point, name='calib_test', iteration_state=IterationState(),
                 sim_runs_per_param_set=1, max_iterations=5, plotters=list()):

        self.name = name
        self.setup = setup
        self.config_builder = config_builder
        self.map_sample_to_model_input_fn = SampleIndexWrapper(map_sample_to_model_input_fn)
        self.sites = sites
        self.next_point = next_point
        self.iteration_state = iteration_state
        self.sim_runs_per_param_set = sim_runs_per_param_set
        self.max_iterations = max_iterations
        self.location = self.setup.get('type')
        self.plotters = [plotter.set_manager(self) for plotter in plotters]
        self.local_suite_id = None
        self.comps_suite_id = None
        self.all_results = None
        self.exp_manager = None
        self.calibration_start = None
        self.iteration_start = None
        self.iter_step = ''
        self.status = ResumePoint.iteration_start
        self.latest_iteration = 0

    def run_calibration(self, **kwargs):
        """
        Create and run a complete multi-iteration calibration suite.
        """
        # Check experiment name as early as possible
        if not utils.validate_exp_name(self.name):
            exit()

        self.location = self.setup.get('type')
        if 'location' in kwargs:
            kwargs.pop('location')

        self.create_calibration(self.location, **kwargs)
        self.run_iterations(**kwargs)

    def create_calibration(self, location, **kwargs):
        """
        Create the working directory for a new calibration.
        Cache the relevant suite-level information to allow re-initializing this instance.
        """
        try:
            os.mkdir(self.name)
            self.cache_calibration()
        except OSError:
            from time import sleep
            logger.info("Calibration with name %s already exists in current directory" % self.name)
            var = ""
            while var.upper() not in ('R', 'B', 'C', 'P', 'A'):
                var = raw_input('Do you want to [R]esume, [B]ackup + run, [C]leanup + run, Re-[P]lot, [A]bort:  ')

            # Abort
            if var == 'A':
                exit()
            elif var == 'B':
                tstamp = re.sub('[ :.-]', '_', str(datetime.now()))
                shutil.move(self.name, "%s_backup_%s" % (self.name, tstamp))
                self.create_calibration(location)
            elif var == "C":
                self.cleanup()
                self.create_calibration(location)
            elif var == "R":
                self.resume_from_iteration(location=location, **kwargs)
                exit()     # avoid calling self.run_iterations(**kwargs)
            elif var == "P":
                self.replot(iteration=None)
                exit()     # avoid calling self.run_iterations(**kwargs)

    @staticmethod
    def retrieve_iteration_state(iter_directory):
        """
        Retrieve IterationState from a given directory
        """
        if not os.path.isdir(iter_directory):
            raise Exception('Unable to find calibration iteration in directory: %s' % iter_directory)

        try:
            return IterationState.from_file(os.path.join(iter_directory, 'IterationState.json'))

        except IOError:
            raise Exception('Unable to find metadata in %s/IterationState.json' % iter_directory)

    def run_iterations(self, **kwargs):
        """
        Run the iteration loop consisting of the following steps:
           * getting parameters to sample from next-point algorithm
             (based on results evaluated from previous iterations)
           * commissioning simulations corresponding to these samples
           * evaluating the results at each sample point by comparing
             the simulation output to appropriate reference data
           * updating the next-point algorithm with sample-point results
             and either truncating or generating next sample points.
        """
        # Start the calibration time
        # DJK: On resume, calibration_start will be over-written.  Is it worth trying to add up the total time?
        #      How much time was algorithm vs. simulation/HPC?
        self.calibration_start = datetime.now().replace(microsecond=0)

        while self.iteration < self.max_iterations:

            self.status = ResumePoint.iteration_start

            # Restart the time for each iteration
            self.iteration_start = datetime.now().replace(microsecond=0)

            logger.info('---- Starting Iteration %d ----' % self.iteration)

            # Make a backup only in resume case!
            self.cache_iteration_state(backup_existing=(self.iteration_state.resume_point.value > 0))

            # Output verbose resume point
            if self.iteration_state.resume_point.value > ResumePoint.iteration_start.value:
                logger.info('-- Resuming Point %d (%s) --' % (self.iteration_state.resume_point.value, self.iteration_state.resume_point.name.title()))

            self.status = ResumePoint.commission
            self.cache_calibration()

            # Start from simulation
            if self.iteration_state.resume_point.value <= ResumePoint.commission.value:
                # for OptimTool, n_dimension is not defined yet.
                next_params = self.get_and_cache_samples_for_this_iteration()
                self.commission_iteration(next_params, **kwargs)
                self.status = ResumePoint.analyze
                self.cache_calibration()

                self.plot_iteration()

            # Start from analyze
            if self.iteration_state.resume_point.value <= ResumePoint.analyze.value:
                self.wait_for_finished()    # Moved wait for finished here
                results = self.analyze_iteration()
                self.give_results_to_next_point_and_cache(results)
                self.status = ResumePoint.plot
                self.cache_calibration()

            # DJK: Need another resume point after next point is done?

            if self.iteration_state.resume_point.value <= ResumePoint.plot.value:
                if self.iteration_state.resume_point == ResumePoint.plot:
                    self.next_point.update_iteration(self.iteration)

                self.status = ResumePoint.next_point
                self.plot_iteration()
                self.cache_calibration()

            if self.finished():
                break

            # Start from next iteration
            if self.iteration_state.resume_point.value <= ResumePoint.next_point.value:
                self.status = ResumePoint.next_point

                if self.iteration_state.resume_point == ResumePoint.next_point:
                    self.next_point.update_iteration(self.iteration)

                # Fix iteration issue in Calibration.json (reason: above self.finished() always returns False)
                if self.iteration + 1 < self.max_iterations:
                    self.increment_iteration()
                    # Make sure the following iteration always starts from very beginning as normal iteration!
                    self.iteration_state.resume_point = ResumePoint.iteration_start
                else:
                    # fix bug: next_point is not updated with the latest results for the last iteration!
                    self.iteration_state.next_point = self.next_point.get_state()
                    self.cache_iteration_state()
                    break

        # Print the calibration finish time
        current_time = datetime.now()
        calibration_time_elapsed = current_time - self.calibration_start
        logger.info("Calibration done (took %s)" % verbose_timedelta(calibration_time_elapsed))

        self.finalize_calibration()

    def get_and_cache_samples_for_this_iteration(self):
        """
        Query the next-point algorithm for the next set of sample points.
        """
        # DJK TODO: Consistentcy of parameters vs points --> USE SAMPLES
        # The following is now a dataframe so that datatype can be preserved (ideally, it's challenging with pandas)
        samples_for_this_iteration = self.next_point.get_samples_for_iteration(self.iteration)
        samples_for_this_iteration.reset_index(drop=True, inplace=True) # Make sure the index, which will become __sample_index__, starts at 0
        assert( isinstance(samples_for_this_iteration, pd.DataFrame) )

        dtypes = {name:str(data.dtype) for name, data in samples_for_this_iteration.iteritems()}
        self.iteration_state.samples_for_this_iteration_dtypes = dtypes # Argh

        # samples_for_this_iteration[ samples_for_this_iteration.isnull() ] = None # DJK: Is this is necessary on Windows?
        samples_NaN_to_Null = samples_for_this_iteration.where(~samples_for_this_iteration.isnull(), other=None)
        self.iteration_state.samples_for_this_iteration = samples_NaN_to_Null.to_dict(orient='list')

        self.iteration_state.next_point = self.next_point.get_state()
        self.cache_iteration_state()
        return samples_for_this_iteration

    def commission_iteration(self, next_params, **kwargs):
        # DJK: This needs to be encapsulated so we can commission other models or even deterministic functions
        """
        Commission an experiment of simulations constructed from a list of combinations of
        random seeds, calibration sites, and the next sample points.
        Cache the relevant experiment and simulation information to the IterationState.
        """

        if self.iteration_state.simulations:
            logger.info('Reloading simulation data from cached iteration (%s) state.' % self.iteration_state.iteration)
            self.exp_manager = ExperimentManagerFactory.from_experiment(DataStore.get_experiment(self.iteration_state.experiment_id))
        else:
            if 'location' in kwargs:
                kwargs.pop('location')

            self.exp_manager = ExperimentManagerFactory.from_setup(self.setup, **kwargs)

            # Generate the suite ID if not present
            if (self.location == "LOCAL" and not self.local_suite_id) or (self.location=="HPC" and not self.comps_suite_id):
                self.generate_suite_id(self.exp_manager)

            exp_builder = ModBuilder.from_combos(
                [ModFn(self.config_builder.__class__.set_param, 'Run_Number', i) for i in range(self.sim_runs_per_param_set)],
                [ModFn(site.setup_fn) for site in self.sites],
                # itertuples preserves datatype
                # First tuple element is index (use this instead of enumerate)
                # Because parameter names are not necessarily valid python identifiers, have to build my own dictionary here
                [ModFn(self.map_sample_to_model_input_fn(sample[0]),
                    {k: v for k, v in zip(next_params.columns.values, sample[1:])})
                 for sample in next_params.itertuples()])

            self.exp_manager.run_simulations(
                config_builder=self.config_builder,
                exp_name='%s_iter%d' % (self.name, self.iteration),
                exp_builder=exp_builder,
                suite_id=self.local_suite_id if self.location == "LOCAL" else self.comps_suite_id)
                #,analyzers=analyzers)

            self.iteration_state.simulations = self.exp_manager.experiment.toJSON()['simulations']
            self.iteration_state.experiment_id = self.exp_manager.experiment.exp_id
            self.cache_iteration_state()

    def wait_for_finished(self, verbose=True, init_sleep=1.0, sleep_time=10):
        while True:
            time.sleep(init_sleep)

            # Output time info
            current_time = datetime.now()
            iteration_time_elapsed = current_time - self.iteration_start
            calibration_time_elapsed = current_time - self.calibration_start

            logger.info('\n\nCalibration: %s' % self.name)
            logger.info('Calibration started: %s' % self.calibration_start)
            logger.info('Current iteration: Iteration %s' % self.iteration)
            logger.info('Current Iteration Started: %s' % self.iteration_start)
            logger.info('Time since iteration started: %s' % verbose_timedelta(iteration_time_elapsed))
            logger.info('Time since calibration started: %s\n' % verbose_timedelta(calibration_time_elapsed))

            # Retrieve simulation status and messages
            try:
                states, msgs = self.exp_manager.get_simulation_status()
            except Exception as ex:
                # logger.info(ex)
                logger.error('Cannot get simulation status. Calibration cannot continue. Exiting...' % self.location)
                logger.error(ex)
                exit()

            # Separate Failed from Canceled case, so that we can handle the following situation later:
            #   If some simulations failed, we may continue...

            # If Calibration has been canceled -> exit
            if self.exp_manager.any_canceled(states) or self.exp_manager.any_failed(states):
                from dtk.utils.ioformat.OutputMessage import OutputMessage
                # Kill the remaining simulations
                OutputMessage("One or more simulations failed/cancelled. Calibration cannot continue. Exiting...")
                self.kill()
                exit()

            # Test if we are all done
            if self.exp_manager.status_finished(states):
                break
            else:
                if verbose:
                    self.exp_manager.print_status(states, msgs)
                time.sleep(sleep_time)

        # Print the status one more time
        iteration_time_elapsed = current_time - self.iteration_start
        logger.info("Iteration %s done (took %s)" % (self.iteration, verbose_timedelta(iteration_time_elapsed)))
        self.exp_manager.print_status(states, msgs)

        # Wait when we are all done to make sure all the output files have time to get written
        time.sleep(sleep_time)

    def analyze_iteration(self):
        """
        Analyze the output of completed simulations by using the relevant analyzers by site.
        Cache the results that are returned by those analyzers.
        """

        if self.iteration_state.results:
            logger.info('Reloading results from cached iteration state.')
            return self.iteration_state.results['total']
        if self.exp_manager:
            exp_manager = self.exp_manager
        else:
            exp = retrieve_experiment(self.iteration_state.experiment_id, verbose=True)
            exp_manager = ExperimentManagerFactory.from_experiment(exp)

        for site in self.sites:
            for analyzer in site.analyzers:
                exp_manager.add_analyzer(analyzer)
        exp_manager.analyze_experiment()

        cached_analyses = {a.uid(): a.cache() for a in exp_manager.analyzers}
        logger.debug(cached_analyses)

        results = pd.DataFrame({a.uid(): a.result for a in exp_manager.analyzers})
        results['total'] = results.sum(axis=1)

        logger.debug(results)
        cached_results = results.to_dict(orient='list')

        self.iteration_state.analyzers = cached_analyses
        self.iteration_state.results = cached_results

        iteration_summary = self.iteration_state.summary_table()

        self.all_results = pd.concat((self.all_results, iteration_summary)).sort_values(by='total', ascending=False)
        logger.info(self.all_results[['iteration', 'total']].head(10))

        self.cache_calibration()
        self.cache_iteration_state()

        return results.total.tolist()

    def plot_iteration(self):
        # Run all the plotters
        map(lambda plotter: plotter.visualize(), self.plotters)
        gc.collect()

    def give_results_to_next_point_and_cache(self, results):
        """
        Pass the latest evaluated results back to the next-point algorithm,
        which will update its state to either truncate the calibration
        or generate the next set of sample points.
        """
        self.next_point.set_results_for_iteration(self.iteration, results)
        self.iteration_state.next_point = self.next_point.get_state()
        self.cache_iteration_state()

    def finished(self):
        """ The next-point algorithm has reached its termination condition. """
        return self.next_point.end_condition()

    def increment_iteration(self):
        """ Cache the last iteration state and initialize a new iteration. """
        self.cache_iteration_state()
        self.iteration_state.increment_iteration()
        self.cache_calibration()  # to update latest iteration

    def finalize_calibration(self):
        """ Get the final samples (and any associated information like weights) from algo. """
        final_samples = self.next_point.get_final_samples()
        logger.debug('Final samples:\n%s', pprint.pformat(final_samples))
        self.cache_calibration(**final_samples)


    def generate_suite_id(self, exp_manager):
        """
        Get a new Suite ID from the LOCAL/HPC ExperimentManager
        and cache to calibration with this updated info.
        """
        if self.location == "LOCAL":
            self.local_suite_id = exp_manager.create_suite(self.name)
        elif self.location == "HPC":
            self.comps_suite_id = exp_manager.create_suite(self.name)
        self.cache_calibration()

    def cache_calibration(self, **kwargs):
        """
        Cache information about the CalibManager that is needed to resume after an interruption.
        N.B. This is not currently the complete state, some of which relies on nested and frozen functions.
             As such, the 'resume' logic relies on the existence of the original configuration script.
        """

        # TODO: resolve un-picklable nested SetupFunctions.set_calibration_site for self.sites
        #       and frozen scipy.stats functions in MultiVariatePrior.function for self.next_point
        state = {'name': self.name,
                 'location': self.location,
                 'local_suite_id': self.local_suite_id,
                 'comps_suite_id': self.comps_suite_id,
                 'iteration': self.iteration,
                 'status': self.status.name,
                 'param_names': self.param_names(),
                 'sites': self.site_analyzer_names(),
                 'results': self.serialize_results(),
                 'setup_overlay_file':self.setup.setup_file,
                 'selected_block': self.setup.selected_block}
        state.update(kwargs)
        json.dump(state, open(os.path.join(self.name, 'CalibManager.json'), 'wb'), indent=4, cls=NumpyEncoder)

    def backup_calibration(self):
        """
        Backup CalibManager.json for resume action
        """
        calibration_path = os.path.join(self.name, 'CalibManager.json')
        if os.path.exists(calibration_path):
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now().replace(microsecond=0)))
            shutil.copy(calibration_path, os.path.join(self.name, 'CalibManager_%s.json' % backup_id))

    def cache_iteration_state(self, backup_existing=False):
        """
        Cache information about the IterationState that is needed to resume after an interruption.
        If resuming from an existing iteration, also copy to backup the initial cached state.
        """
        iter_directory = ""
        try:
            iter_directory = self.iteration_directory()
            os.makedirs(iter_directory)
        except OSError:
            pass

        iter_state_path = os.path.join(iter_directory, 'IterationState.json')
        if backup_existing and os.path.exists(iter_state_path):
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now().replace(microsecond=0)))
            os.rename(iter_state_path, os.path.join(iter_directory, 'IterationState_%s.json' % backup_id))

        self.iteration_state.to_file(iter_state_path)

    def serialize_results(self):
        if self.all_results is None:
            return []

        if not isinstance(self.all_results, pd.DataFrame):
            raise Exception('all_results must be a pandas DataFrame')

        self.all_results.index.name = 'sample'
        data = self.all_results.reset_index()

        data.iteration = data.iteration.astype(int)
        data['sample'] = data['sample'].astype(int)

        return data.to_dict(orient='list')

    def restore_results(self, results, iteration):
        """
        Restore summary results from serialized state.
        """

        if not results:
            logger.debug('No cached results to reload from CalibManager.')
            return

        self.all_results = pd.DataFrame.from_dict(results, orient='columns')
        self.all_results.set_index('sample', inplace=True)

        self.all_results = self.all_results[self.all_results.iteration <= iteration]
        logger.debug(self.all_results)

    def check_leftover(self):
        """
            - Handle the case: process got interrupted but it still runs on remote
            - Handle location change case: may resume from commission instead
        """
        # Step 1: Checking possible location changes
        try:
            exp_id = self.iteration_state.experiment_id
            exp = retrieve_experiment(exp_id)
        except Exception as ex:
            exp = None
            import traceback
            traceback.print_exc()

        if not exp:
            var = raw_input("Cannot restore Experiment 'exp_id: %s'. Force to resume from commission... Continue ? [Y/N]" % exp_id if exp_id else 'None')
            # force to resume from commission
            if var.upper() == 'Y':
                self.iter_step = 'commission'
            else:
                logger.info("Answer is '%s'. Exiting...", var.upper())
                exit()

        # If location has been changed, will double check user for a special case before proceed...
        if self.location != exp.location and self.iter_step in ['analyze', 'plot', 'next_point']:
            var = raw_input("Location has been changed from '%s' to '%s'. Resume will start from commission instead, do you want to continue? [Y/N]:  " % (exp.location, self.location))
            if var.upper() == 'Y':
                self.iter_step = 'commission'
            else:
                logger.info("Answer is '%s'. Exiting...", var.upper())
                exit()

        # Step 2: Checking possible leftovers
        try:
            # Save the selected block the user wants
            user_selected_block = self.setup.selected_block
            # Retrieve the experiment manager. Note: it changed selected_block
            self.exp_manager = ExperimentManagerFactory.from_experiment(exp)
            # Restore the selected block
            self.setup.selected_block = user_selected_block
        except Exception:
            logger.info('Proceed without checking the possible leftovers.')
            # Restore the selected block
            self.setup.selected_block = user_selected_block
            return

        # Don't do the leftover checking for a special case
        if self.iter_step == 'commission':
            return

        # Make sure it is finished
        self.exp_manager.wait_for_finished(verbose=True)

        try:
            # check the status
            states = self.exp_manager.get_simulation_status()[0]
        except Exception as ex:
            # logger.info(ex)
            logger.info('Proceed without checking the possible leftovers.')
            return

        if not states:
            logger.info('Proceed without checking the possible leftovers.')
            return


    def prepare_resume_point_for_iteration(self, iteration):
        """
        Setup resume point the point to resume the iteration:
           * commission -- commission a new iteration of simulations based on existing next_params
           * analyze -- calculate results for an existing iteration of simulations
           * next_point -- generate next sample points from an existing set of results
        """
        # Restore current iteration and next_point
        self.restore_next_point_for_iteration(iteration)

        # Check leftover (in case lost connection) and also consider possible location change.
        self.check_leftover()

        # Adjust resuming point based on input options
        if self.iter_step:
            self.adjust_resume_point(iteration)

        # transfer the final resume point
        self.iteration_state.resume_point = self.status

        # Prepare iteration state
        if self.iteration_state.resume_point == ResumePoint.commission:
            # need to run simulations
            self.iteration_state.simulations = {}
            self.iteration_state.results = {}
        elif self.iteration_state.resume_point == ResumePoint.analyze:
            # just need to calculate the results
            self.iteration_state.results = {}
        elif self.iteration_state.resume_point == ResumePoint.plot:
            # just need to do plotting based on the existing results
            pass
        elif self.iteration_state.resume_point == ResumePoint.next_point:
            pass
        else:
            pass

        # adjust next_point
        self.restore_next_point()

    def restore_calibration_for_resume(self, calib_data, iteration):
        if not calib_data:
            calib_data = self.read_calib_data()

        self.local_suite_id = calib_data.get('local_suite_id')
        self.comps_suite_id = calib_data.get('comps_suite_id')

        if self.iteration_state.resume_point.value < ResumePoint.plot.value:
            # it will combine current results with previous results
            self.restore_results(calib_data.get('results'), iteration - 1)
        else:
            # it will use the current results and resume from next iteration
            self.restore_results(calib_data.get('results'), iteration)

    def restore_next_point(self):
        """
        Restore next_point up to this iteration
        Note: when come to here:
                - self.iteration_state has been restored from current self.iteration already!
                - self.next_point has been restored from current self.iteration already!
        """
        # Handel the general cases for resume
        if self.iteration_state.resume_point == ResumePoint.commission:
            # Note: later will generate new samples. Need to clean up next_point for resume from commission.
            if self.iteration == 0:
                self.next_point.cleanup()
            elif self.iteration > 0:
                # Now we need to restore next_point from previous iteration (need to re-generate new samples late)
                iteration_state = IterationState.restore_state(self.name, self.iteration - 1)
                self.next_point.set_state(iteration_state.next_point, self.iteration - 1)

            # prepare and ready for new experiment and simulations
            self.iteration_state.reset_state()
        elif self.iteration_state.resume_point == ResumePoint.analyze:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            if self.iteration == 0:
                self.next_point.cleanup()
            elif self.iteration > 0:
                # Now, we need to restore gaussian from previous iteration
                iteration_state = IterationState.restore_state(self.name, self.iteration - 1)
                self.next_point.restore(iteration_state)
        elif self.iteration_state.resume_point == ResumePoint.plot:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            pass
        elif self.iteration_state.resume_point == ResumePoint.next_point:
            # Note: self.next_point has been already restored from current iteration, move on to next iteration!
            pass
        else:
            # in case we have more resuming point in the future
            pass

    def restore_next_point_for_iteration(self, iteration):
        """
        Restore next_point up to this iteration
        """
        # Restore IterationState and keep the resume_point
        resume_point = self.iteration_state.resume_point
        self.iteration_state = IterationState.restore_state(self.name, iteration)
        self.iteration_state.resume_point = resume_point

        # Update next point
        self.next_point.set_state(self.iteration_state.next_point, iteration)

        # Store iteration #:
        self.iteration_state.iteration = iteration

    def adjust_resume_point(self, iteration):
        """
        Consider user's input and determine the resuming point
        """

        input_resume_point = ResumePoint[self.iter_step]

        if self.latest_iteration == iteration:
            # user input iter_step may not be valid
            if input_resume_point.value <= self.status.value:
                self.status = input_resume_point
            else:
                logger.info("The farthest resume point available is '%s', we will resume from it instead of '%s'" \
                      % (self.status.name, input_resume_point.name))
                answer = raw_input("Continue ? [Y/N]")
                if answer != "Y": exit()
        else:
            # just take user input iter_step
            self.status = input_resume_point

    def find_best_iteration_for_resume(self, iteration=None, calib_data=None):
        """
        Find the latest good iteration from where we can do resume
        """
        # If calib_data is None or Empty, throw exception
        if calib_data is None or not calib_data:
            raise Exception('Metadata is empty in %s/CalibManager.json' % self.name)

        # If calib_data has no results, will resume from Iteration 0
        if not calib_data.get('results', {}):
            return 0

        # If no iteration passed in, take latest_iteration for resume
        if iteration is None:
            iteration = self.latest_iteration

        # Adjust input iteration
        if self.latest_iteration < iteration:
            iteration = self.latest_iteration

        return iteration

    def resume_from_iteration(self, iteration=None, iter_step=None, **kwargs):
        """
        It takes several steps:
          * First we need to find the latest 'best' iteration
          * Then restore IterationState for this iteration and check the resuming point
          * Restore the proper results for resume
          * Finally got through the iteration loop
        """
        if not os.path.isdir(self.name):
            raise Exception('Unable to find existing calibration in directory: %s' % self.name)

        # Make a backup of CalibManager.json
        self.backup_calibration()

        # Keep iter_step which will be used later to determine the Resuming Point
        self.iter_step = iter_step.lower() if iter_step is not None else ''

        # Keep the simulation type: LOCAL, HPC, ...
        self.location = self.setup.get('type')

        calib_data = self.read_calib_data()
        self.status = ResumePoint[calib_data.get('status', ResumePoint.iteration_start.name)]
        self.latest_iteration = int(calib_data.get('iteration', 0))
        iteration = self.find_best_iteration_for_resume(iteration, calib_data)

        self.prepare_resume_point_for_iteration(iteration)
        self.restore_calibration_for_resume(calib_data, iteration)

        # enter iteration loop
        self.run_iterations(**kwargs)

        # check possible leftover experiments
        self.check_orphan_experiments()

        # delete all backup file for CalibManger and each of iterations
        self.cleanup_backup_files()

    def replot(self, iteration):
        # change this to replot all and leverage below per-iteration function
        logger.info('Start Re-Plot Process!')

        # make sure data exists for plotting
        if not os.path.isdir(self.name):
            raise Exception('Unable to find existing calibration in directory: %s' % self.name)

        # restore the existing calibration data
        calib_data = self.read_calib_data()
        self.latest_iteration = int(calib_data.get('iteration', 0))

        # restore calibration results
        results = calib_data.get('results')
        if not results:
            logger.info('No iteration cached results to reload from CalibManager.')
            return

        # restore results as DataFrame
        local_all_results = pd.DataFrame.from_dict(results, orient='columns')
        logger.info('latest_iteration = %s' % self.latest_iteration)

        if iteration is not None:
            assert(iteration <= self.latest_iteration)
            self.replot_iteration(iteration, local_all_results)
            return

        # replot for each iteration up to latest
        for i in range(0, self.latest_iteration + 1):
            self.replot_iteration(i, local_all_results)

    def replot_iteration(self, iteration, local_all_results):
        # replot for each iteration up to latest
        logger.info('Re-plotting for iteration: %d' % iteration)

        # restore current iteration state
        iter_directory = os.path.join(self.name, 'iter%d' % iteration)
        self.iteration_state = self.retrieve_iteration_state(iter_directory)

        # restore next point
        self.next_point.set_state(self.iteration_state.next_point, iteration)

        # restore all_results for current iteration
        self.all_results = local_all_results[local_all_results.iteration <= iteration]

        for plotter in self.plotters:
            if isinstance(plotter, SiteDataPlotter.SiteDataPlotter) and iteration != self.latest_iteration:
                continue
            plotter.visualize(self)
            gc.collect() # Have to clean up after matplotlib is done

    def load_experiment_from_iteration(self, iteration=None):
        """
        Load experiment for a given or the latest iteration
        """
        if iteration is None:
            # restore the existing calibration data
            calib_data = self.read_calib_data()

            # Get the last iteration
            latest_iteration = calib_data.get('iteration', None)
        else:
            latest_iteration = iteration

        # Restore IterationState
        it = IterationState.from_file(os.path.join(self.name, 'iter%d' % latest_iteration, 'IterationState.json'))

        # Get experiment by id
        return DataStore.get_experiment(it.experiment_id)

    def kill(self):
        """
        Kill the current calibration
        """
        exp = self.load_experiment_from_iteration()

        # Cancel simulations for all active managers
        exp_manager = ExperimentManagerFactory.from_experiment(exp)
        exp_manager.cancel_experiment()

        # Print confirmation
        logger.info("Calibration %s successfully cancelled!" % self.name)

    def cleanup(self):
        """
        Cleanup the current calibration
        - Delete the result directory
        - If LOCAL -> also delete the simulations
        """
        # Save the selected block the user wants
        user_selected_block = self.setup.selected_block

        try:
            calib_data = self.read_calib_data()
        except Exception:
            logger.info('Calib data cannot be read -> skip')
            calib_data = None
            comps_suite = None

        if calib_data:
            # Retrieve suite ids and iter_count
            comps_suite = calib_data.get('comps_suite_id')
            local_suite = calib_data.get('local_suite_id')
            iter_count = calib_data.get('iteration')

            # Also retrieve the selected block
            self.setup.override_block(calib_data['selected_block'])

            # Delete the simulations too
            logger.info('Cleaning up calibration %s' % self.name)
            for i in range(0, iter_count + 1):
                # Get the iteration cache
                iteration_cache = os.path.join(self.name, 'iter%d' % i, 'IterationState.json')

                if not os.path.exists(iteration_cache):
                    break
                # Retrieve the iteration state
                it = IterationState.from_file(iteration_cache)

                # Create the associated experiment manager and ask for deletion
                try:
                    exp_mgr = ExperimentManagerFactory.from_experiment(DataStore.get_experiment(it.experiment_id))
                    exp_mgr.hard_delete()
                except:
                    continue

            # Delete all associated experiments in db
            DataStore.delete_experiments_by_suite([local_suite, comps_suite])

        # Then delete the whole directory
        calib_dir = os.path.abspath(self.name)
        if os.path.exists(calib_dir):
            try:
                shutil.rmtree(calib_dir)
            except OSError:
                logger.error("Failed to delete %s" % calib_dir)

        # To finish delete the COMPS suite
        if comps_suite:
            logger.info('Delete COMPS suite %s' % comps_suite)
            utils.COMPS_login(self.setup.get('server_endpoint'))
            from simtools.Utilities.COMPSUtilities import delete_suite
            delete_suite(comps_suite)

        # Restore the selected block
        self.setup.override_block(user_selected_block)


    def reanalyze(self):
        """
        Reanalyze the current calibration
        """
        calib_data = self.read_calib_data()

        # Override our setup with what is in the file
        self.setup.override_block(calib_data['selected_block'])
        self.location = self.setup.get('type')

        if calib_data['location'] == 'HPC':
            utils.COMPS_login(self.setup.get('server_endpoint'))

        # Cleanup the LL_all.csv
        if os.path.exists(os.path.join(self.name, 'LL_all.csv')):
            os.remove(os.path.join(self.name, 'LL_all.csv'))

        # Get the count of iterations and save the suite_id
        iter_count = calib_data.get('iteration')
        logger.info("Reanalyze will go through %s iterations." % (iter_count+1))

        # Go through each already ran iterations
        for i in range(0, iter_count+1):
            self.reanalyze_iteration(i)

        # Before leaving -> set back the suite_id
        self.local_suite_id = calib_data.get('local_suite_id')
        self.comps_suite_id = calib_data.get('comps_suite_id')
        self.location = calib_data['location']

        # Also finalize
        self.finalize_calibration()

    def reanalyze_iteration(self, iteration):
        logger.info("\nReanalyze Iteration %s" % iteration)
        # Create the path for the iteration dir
        iter_directory = os.path.join(self.name, 'iter%d' % iteration)

        # Create the state for the current iteration
        self.iteration_state = self.retrieve_iteration_state(iter_directory)
        self.next_point.set_state(self.iteration_state.next_point, iteration)

        self.iteration_state.iteration = iteration

        # Empty the results and analyzers
        self.iteration_state.results = {}
        self.iteration_state.analyzers = {}

        self.status = ResumePoint.analyze
        self.plot_iteration()

        # Analyze again!
        res = self.analyze_iteration()

        # Call all plotters
        self.status = ResumePoint.next_point
        self.plot_iteration()

        logger.info("Iteration %s reanalyzed." % iteration)

    def read_calib_data(self, force=False):
        try:
            return json.load(open(os.path.join(self.name, 'CalibManager.json'), 'rb'))
        except IOError:
            if not force:
                raise Exception('Unable to find metadata in %s/CalibManager.json' % self.name)
            else:
                return None

    def get_experiment_from_iteration(self, iteration=None, force_metadata=False):
        """
        Retrieve experiment for a given iteration
        """
        exp = None

        # Only check iteration for resume cases
        if force_metadata:
            iteration = self.adjust_iteration(iteration)
            iteration_cache = os.path.join(self.name, 'iter%d' % iteration, 'IterationState.json')
            it = IterationState.from_file(iteration_cache)

            exp = DataStore.get_experiment(it.experiment_id)

        return exp

    def adjust_iteration(self, iteration=None, calib_data=None):
        """
        Validate iteration against latest_iteration
        return adjusted iteration
        """
        # If calib_data is None or Empty, load data
        if calib_data is None or not calib_data:
            calib_data = self.read_calib_data()

        # Get latest iteration #
        latest_iteration = calib_data.get('iteration', None)

        # Handle special case
        if latest_iteration is None:
            return 0

        # If no iteration passed in, take latest_iteration as instead
        if iteration is None:
            iteration = latest_iteration

        # Adjust input iteration
        if latest_iteration < iteration:
            iteration = latest_iteration

        return iteration

    def check_orphan_experiments(self, ask=True):
        """
            - Display all orphan experiments for this calibration
            - Provide user option to clean up
        """
        if not ask:
            self.clear_orphan_experiments()
            return

        # Continue if ask == True
        exp_orphan_list = self.list_orphan_experiments()
        if exp_orphan_list is None or len(exp_orphan_list) == 0:
            return

        orphan_str_list = ['- %s - %s' % (exp.exp_id, exp.exp_name) for exp in exp_orphan_list]
        logger.info('\nOrphan Experiment List:')
        logger.info('\n'.join(orphan_str_list))
        logger.info('\n')

        DataStore.delete_experiments(exp_orphan_list)
        if len(exp_orphan_list) > 1:
            logger.info('Note: the detected orphan experiments have been deleted.')
        else:
            logger.info('Note: the detected orphan experiment has been deleted.')

    def clear_orphan_experiments(self):
        """
        Cleanup the experiments in db, which are associated with THIS calibration's
        suite_id and exp_ids
        """
        # make sure data exists
        if not os.path.isdir(self.name):
            logger.info('Unable to find existing calibration in directory (%s), no experiments cleanup is processed.', self.name)
            return

        suite_ids, exp_ids = self.get_experiments()
        DataStore.clear_leftover(suite_ids, exp_ids)

    def cleanup_backup_files(self):
        """
        Cleanup the backup files for current calibration
        """
        def delete_files(file_list):
            # print '\n'.join(file_list)
            for f in file_list:
                if os.path.exists(f):
                    try:
                        os.remove(f)
                    except OSError:
                        logger.error("Failed to delete %s" % f)

        iter_count = self.iteration
        if iter_count is None:
            try:
                calib_data = self.read_calib_data()
                iter_count = calib_data.get('iteration', 0)
            except Exception:
                logger.info('Calib data cannot be read, no backup files are deleted.')
                return

        # Step 1: delete backup files for each of the iterations
        for i in range(0, iter_count + 1):
            # Get the iteration backup files
            iteration_cache = os.path.join(self.name, 'iter%d' % i, 'IterationState_backup_*.json')
            backup_files = glob.glob(iteration_cache)
            if backup_files is None or len(backup_files) == 0:
                continue

            delete_files(backup_files)

        # Step 2: delete backup files for CalibManger.json
        # Get the CalibManager backup files
        calib_manager_cache = os.path.join(self.name, 'CalibManager_backup_*.json')
        backup_files = glob.glob(calib_manager_cache)
        if backup_files is None or len(backup_files) == 0:
            return

        delete_files(backup_files)

    def list_orphan_experiments(self):
        """
        Get orphan experiment list for this calibration
        """
        suite_ids, exp_ids = self.get_experiments()
        exp_orphan_list = DataStore.list_leftover(suite_ids, exp_ids)
        return exp_orphan_list

    def get_experiments(self):
        """
        Retrieve suite_ids and their associated exp_ids
        """
        # restore the existing calibration data
        calib_data = self.read_calib_data()
        latest_iteration = calib_data.get('iteration')

        exp_ids = []
        for i in range(0, latest_iteration + 1):
            iter_dir = os.path.join(self.name, 'iter%d' % i)
            iter_path = os.path.join(iter_dir, 'IterationState.json')
            if not os.path.exists(iter_path):
                continue

            iter_data = json.load(open(iter_path, 'rb'))
            exp_id = iter_data.get('experiment_id', None)
            if exp_id:
                exp_ids.append(exp_id)

        return [calib_data.get('local_suite_id'), calib_data.get('comps_suite_id')], exp_ids

    @property
    def iteration(self):
        return self.iteration_state.iteration

    def iteration_directory(self):
        return os.path.join(self.name, 'iter%d' % self.iteration)

    def state_for_iteration(self, iteration):
        iter_directory = os.path.join(self.name, 'iter%d' % iteration)
        return IterationState.from_file(os.path.join(iter_directory, 'IterationState.json'))

    def param_names(self):
        return self.next_point.get_param_names()

    def site_analyzer_names(self):
        return {site.name: [a.name for a in site.analyzers] for site in self.sites}