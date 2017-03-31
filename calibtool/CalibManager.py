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
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder, ModFn
from simtools.Utilities.COMPSUtilities import COMPS_login
from simtools.Utilities.Encoding import NumpyEncoder
from simtools.Utilities.Experiments import validate_exp_name, retrieve_experiment
from simtools.Utilities.General import init_logging
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager

logger = init_logging("Calibration")


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
        self.iteration_state.working_directory = self.name
        self.sim_runs_per_param_set = sim_runs_per_param_set
        self.max_iterations = max_iterations
        self.location = self.setup.get('type')
        self.plotters = [plotter.set_manager(self) for plotter in plotters]
        self.suites = []
        self.all_results = None
        self.exp_manager = None
        self.calibration_start = None
        self.iteration_start = None
        self.iter_step = ''
        self.status = ResumePoint.iteration_start
        self.latest_iteration = 0

    @property
    def suite_id(self):
        # Generate the suite ID if not present
        if not self.suites or self.suites[-1]['type'] != self.location:
            suite_id = self.exp_manager.create_suite(self.name)
            self.suites.append({'id':suite_id, 'type':self.location})
            self.cache_calibration()

        return self.suites[-1]['id']

    def run_calibration(self, **kwargs):
        """
        Create and run a complete multi-iteration calibration suite.
        """
        # Check experiment name as early as possible
        if not validate_exp_name(self.name):
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
            # START_STEP
            self.starting_step()

            # COMMISSION STEP
            if self.iteration_state.commission_check():
                self.commission_step(**kwargs)

            # ANALYZE STEP
            if self.iteration_state.analyze_check():
                self.analyze_step()

            # PLOTTING STEP
            if self.iteration_state.plotting_check():
                self.plotting_step()

            # Done with calibration? exit the loop
            if self.finished():
                break

            # Start from next iteration
            if self.iteration_state.next_point_check():
                # NEXT STEP
                if not self.next_step():
                    break

        # Print the calibration finish time
        current_time = datetime.now()
        calibration_time_elapsed = current_time - self.calibration_start
        logger.info("Calibration done (took %s)" % verbose_timedelta(calibration_time_elapsed))

        self.finalize_calibration()

    def next_step(self):
        self.next_point_step()

        # Fix iteration issue in Calibration.json (reason: above self.finished() always returns False)
        if self.iteration + 1 < self.max_iterations:
            self.increment_iteration()
            # Make sure the following iteration always starts from very beginning as normal iteration!
            self.iteration_state.resume_point = ResumePoint.iteration_start
            return True
        else:
            # fix bug: next_point is not updated with the latest results for the last iteration!
            self.iteration_state.set_next_point(self.next_point)
            return False

    def starting_step(self):
        self.status = ResumePoint.iteration_start

        # Restart the time for each iteration
        self.iteration_start = datetime.now().replace(microsecond=0)

        logger.info('---- Starting Iteration %d ----' % self.iteration)

        # Make a backup only in resume case!
        self.iteration_state.save(backup_existing=(self.iteration_state.resume_point.value > 0))

        # Output verbose resume point
        if self.iteration_state.resume_point.value > ResumePoint.iteration_start.value:
            logger.info('-- Resuming Point %d (%s) --' % (
            self.iteration_state.resume_point.value, self.iteration_state.resume_point.name.title()))

        self.status = ResumePoint.commission
        self.cache_calibration()

    def commission_step(self, **kwargs):
        # Get the params from the next_point
        next_params = self.next_point.get_samples_for_iteration(self.iteration)
        self.iteration_state.set_samples_for_iteration(self.iteration, next_params, self.next_point)

        # Then commission
        self.commission_iteration(next_params, **kwargs)

        # Ready for analyzing
        self.status = ResumePoint.analyze
        self.cache_calibration()

        # Call the plot for post commission plots
        self.plot_iteration()

    def analyze_step(self):
        # Make sure all our simulations finished first
        self.wait_for_finished()

        # Analyze the iteration
        self.analyze_iteration()

        # Ready for plotting
        self.status = ResumePoint.plot
        self.cache_calibration()

    def plotting_step(self):
        if self.iteration_state.resume_point == ResumePoint.plot:
            self.next_point.update_iteration(self.iteration)

        # Ready for next point
        self.status = ResumePoint.next_point
        self.cache_calibration()

        # Plot the iteration
        self.plot_iteration()

    def next_point_step(self):
        self.status = ResumePoint.next_point

        if self.iteration_state.resume_point == ResumePoint.next_point:
            self.next_point.update_iteration(self.iteration)

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

            exp_builder = ModBuilder.from_combos(
                [ModFn(self.config_builder.__class__.set_param, 'Run_Number', i) for i in range(self.sim_runs_per_param_set)],
                [ModFn(site.setup_fn) for site in self.sites],
                [ModFn(self.map_sample_to_model_input_fn(index), samples) for index, samples in enumerate(next_params)]
            )


            self.exp_manager.run_simulations(
                config_builder=self.config_builder,
                exp_name='%s_iter%d' % (self.name, self.iteration),
                exp_builder=exp_builder,
                suite_id=self.suite_id)
                #,analyzers=analyzers)

            self.iteration_state.simulations = self.exp_manager.experiment.toJSON()['simulations']
            self.iteration_state.experiment_id = self.exp_manager.experiment.exp_id
            self.iteration_state.save()

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

            # Display the statuses
            if verbose:
                self.exp_manager.print_status(states, msgs)

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

            time.sleep(sleep_time)

        # Print the status one more time
        iteration_time_elapsed = current_time - self.iteration_start
        logger.info("Iteration %s done (took %s)" % (self.iteration, verbose_timedelta(iteration_time_elapsed)))

        # Wait when we are all done to make sure all the output files have time to get written
        time.sleep(1)

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

        analyzer_list = []
        for site in self.sites:
            for analyzer in site.analyzers:
                analyzer_list.append(analyzer)

        analyzerManager = AnalyzeManager(exp_manager.experiment, analyzer_list, working_dir=self.iteration_directory())
        analyzerManager.analyze()

        # Ask the analyzers to cache themselves
        cached_analyses = {a.uid(): a.cache() for a in analyzerManager.analyzers}
        logger.debug(cached_analyses)

        # Get the results from the analyzers and ask the next point how it wants to cache them
        results = pd.DataFrame({a.uid(): a.result for a in analyzerManager.analyzers})
        cached_results = self.next_point.get_results_to_cache(results)
        logger.debug(cached_results)

        # Store the analyzers and results in the iteration state
        self.iteration_state.analyzers = cached_analyses
        self.iteration_state.results = cached_results

        # Set those results in the next point algorithm
        self.next_point.set_results_for_iteration(self.iteration, results)
        self.iteration_state.set_next_point(self.next_point)

        # Update the summary table and all the results
        all_results, summary_table = self.next_point.update_summary_table(self.iteration_state, self.all_results)
        self.all_results = all_results
        logger.info(summary_table)

        # Cache
        self.cache_calibration()

    def plot_iteration(self):
        # Run all the plotters
        map(lambda plotter: plotter.visualize(), self.plotters)
        gc.collect()

    def finished(self):
        """ The next-point algorithm has reached its termination condition. """
        return self.next_point.end_condition()

    def increment_iteration(self):
        """ Initialize a new iteration. """
        self.iteration_state.increment_iteration()
        self.cache_calibration()  # to update latest iteration

    def finalize_calibration(self):
        """ Get the final samples (and any associated information like weights) from algo. """
        final_samples = self.next_point.get_final_samples()
        logger.debug('Final samples:\n%s', pprint.pformat(final_samples))
        self.cache_calibration(**final_samples)

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
                 'suites': self.suites,
                 'iteration': self.iteration,
                 'status': self.status.name,
                 'param_names': self.param_names(),
                 'sites': self.site_analyzer_names(),
                 'results': self.serialize_results(),
                 'setup_overlay_file':self.setup.setup_file,
                 'selected_block': self.setup.selected_block}
        state.update(kwargs)
        json.dump(state, open(os.path.join(self.name, 'CalibManager.json'), 'wb'), indent=4, cls=NumpyEncoder)

        # Also save the iteration_state
        self.iteration_state.save()

    def backup_calibration(self):
        """
        Backup CalibManager.json for resume action
        """
        calibration_path = os.path.join(self.name, 'CalibManager.json')
        if os.path.exists(calibration_path):
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now().replace(microsecond=0)))
            shutil.copy(calibration_path, os.path.join(self.name, 'CalibManager_%s.json' % backup_id))

    def serialize_results(self):
        if self.all_results is None:
            return []

        if not isinstance(self.all_results, pd.DataFrame):
            return self.all_results

        self.all_results.index.name = 'sample'
        data = self.all_results.reset_index()

        data.iteration = data.iteration.astype(int)
        data['sample'] = data['sample'].astype(int)

        return data.to_dict(orient='list')

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

        # prepare resume status
        self.iteration_state.prepare_resume_state(self, iteration, iter_step)

        # enter iteration loop
        self.run_iterations(**kwargs)

        # remove any leftover experiments
        self.cleanup_orphan_experiments()

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
        if not exp: return

        # Cancel simulations for all active managers
        exp_manager = ExperimentManagerFactory.from_experiment(exp)
        exp_manager.cancel_experiment()

        logger.info("Waiting to complete cancellation...")
        exp_manager.wait_for_finished(verbose=False, sleep_time=1)

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

        if calib_data:
            # Retrieve suite ids and iter_count
            suites = calib_data.get('suites')
            iter_count = calib_data.get('iteration')

            # Also retrieve the selected block
            self.setup.override_block(calib_data['selected_block'])

            # Kill
            self.kill()

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

            # Delete all HPC suites (the local suites are only carried by experiments)
            for suite in suites:
                if suite['type'] == "HPC":
                    logger.info('Delete COMPS suite %s' % suite['id'])
                    COMPS_login(self.setup.get('server_endpoint'))
                    from simtools.Utilities.COMPSUtilities import delete_suite
                    delete_suite(suite['id'])

        # Then delete the whole directory
        calib_dir = os.path.abspath(self.name)
        if os.path.exists(calib_dir):
            try:
                shutil.rmtree(calib_dir)
            except OSError:
                logger.error("Failed to delete %s" % calib_dir)
                logger.error("Try deleting the folder manually before retrying the calibration.")

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
            COMPS_login(self.setup.get('server_endpoint'))

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
        self.suites = calib_data['suites']
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
        self.analyze_iteration()

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

    def cleanup_orphan_experiments(self):
        """
            - Display all orphan experiments for this calibration
            - Hard delete all orphans
        """
        exp_orphan_list = self.list_orphan_experiments()
        for experiment in exp_orphan_list:
            ExperimentManagerFactory.from_experiment(experiment).delete(hard=True)
        
        if len(exp_orphan_list) > 0:
            orphan_str_list = ['- %s - %s' % (exp.exp_id, exp.exp_name) for exp in exp_orphan_list]
            logger.info('\nOrphan Experiment List:')
            logger.info('\n'.join(orphan_str_list))
            logger.info('\n')
            logger.info('Note: the detected orphan experiment(s) have been deleted.')

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

        return [suite['id'] for suite in calib_data['suites']], exp_ids

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