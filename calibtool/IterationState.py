import gc
import json
import os
import re
import time
from datetime import datetime

import pandas as pd

from calibtool.utils import StatusPoint
from core.utils.time import verbose_timedelta
from simtools.AnalyzeManager.AnalyzeManager import AnalyzeManager
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.Utilities.Encoding import json_numpy_obj_hook, NumpyEncoder
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.Utilities.General import init_logging

logger = init_logging("Calibration")


class IterationState:
    """
    Holds the settings, parameters, simulation state, analysis results, etc.
    for one calibtool iteration.

    Allows for the resumption or extension of existing CalibManager instances
    from an arbitrary point in the iterative process.
    """
    def __init__(self, **kwargs):
        self.iteration = 0
        self.calibration_name = None
        self.suite_id = {}
        self.samples_for_this_iteration = {}
        self.next_point = {}
        self.simulations = {}
        self.analyzers = {}
        self.results = {}
        self.experiment_id = None
        self.exp_manager = None
        self.next_point_algo = None
        self.analyzer_list = []
        self.site_analyzer_names = {}
        self.config_builder = None
        self.exp_builder_func = None
        self.plotters = []
        self.all_results = None
        self.summary_table = None
        self.iteration_start = None
        self.calibration_start = None

        if 'calibration_start' in kwargs:
            cs = kwargs.pop('calibration_start')
            if isinstance(cs, unicode): self.calibration_start = datetime.strptime(cs, '%Y-%m-%d %H:%M:%S')
            else: self.calibration_start = cs

        if 'iteration_start' in kwargs:
            cs = kwargs.pop('iteration_start')
            if isinstance(cs, unicode): self.iteration_start = datetime.strptime(cs, '%Y-%m-%d %H:%M:%S')
            else: self.iteration_start = cs

        self._status = None
        self.update(**kwargs)

    @property
    def status(self):
        return self._status

    @status.setter
    def status(self, status):
        self._status = status
        self.save()

    def update(self, **kwargs):
        for k, v in kwargs.items():
            setattr(self, k, v)

    def restore_next_point(self, iter_step):
        """
        Restore next_point up to this iteration
        """
        # initialization and may need adjustment based on resume_point
        self.next_point_algo.set_state(self.next_point, self.iteration)

        # Handel the general cases for resume
        if iter_step == StatusPoint.commission:
            # Note: later will generate new samples. Need to clean up next_point for resume from commission.
            if self.iteration == 0:
                self.next_point_algo.cleanup()
            elif self.iteration > 0:
                # Now we need to restore next_point from previous iteration (need to re-generate new samples late)
                iteration_state = IterationState.restore_state(self.calibration_name, self.iteration - 1)
                self.next_point_algo.set_state(iteration_state.next_point, self.iteration - 1)

            # prepare and ready for new experiment and simulations
            self.reset_state()
        elif iter_step == StatusPoint.analyze:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            if self.iteration == 0:
                self.next_point_algo.cleanup()
            elif self.iteration > 0:
                # Now, we need to restore gaussian from previous iteration
                iteration_state = IterationState.restore_state(self.calibration_name, self.iteration - 1)
                self.next_point_algo.restore(iteration_state)
        elif iter_step == StatusPoint.plot or iter_step == StatusPoint.next_point:
            # Note: self.next_point has been already restored from current iteration, so it has current samples!
            # Note: self.next_point has been already restored from current iteration, move on to next iteration!
            pass

    def restore_results(self, iteration):
        """
        Restore summary results from serialized state.
        """
        # Depending on the type of results (lists or dicts), handle differently how we treat the results
        # This should be refactor to take care of both cases at once
        if isinstance(self.all_results, pd.DataFrame):
            self.all_results.set_index('sample', inplace=True)
            self.all_results = self.all_results[self.all_results.iteration <= iteration]
        elif isinstance(self.all_results, list):
            self.all_results = self.all_results[iteration]

    def resume(self, iter_step):
        # step 1: If we know we are running -> recreate the exp_manager
        if iter_step.value >= StatusPoint.running.value:
            self.exp_manager = ExperimentManagerFactory.from_experiment(retrieve_experiment(self.experiment_id))

        # step 2: restore next_point
        self.restore_next_point(iter_step)

        # step 3: restore Calibration results
        if self.iteration > 0:
            if iter_step.value < StatusPoint.plot.value:
                # it will combine current results with previous results
                self.restore_results(self.iteration - 1)
            else:
                # it will use the current results and resume from next iteration
                self.restore_results(self.iteration)

        # step 4: prepare resume states
        if iter_step == StatusPoint.commission:
            # need to run simulations
            self.simulations = {}
            self.results = {}
        elif iter_step == StatusPoint.analyze:
            # just need to calculate the results
            self.results = {}

        self.status = StatusPoint(iter_step.value - 1) if iter_step.value > 0 else None

    def run(self):
        # START_STEP
        if not self.status:
            self.starting_step()

        # COMMISSION STEP
        if self.status == StatusPoint.iteration_start:
            self.commission_step()

        # RUNNING
        if self.status == StatusPoint.commission:
            self.status = StatusPoint.running
            self.wait_for_finished()

        # ANALYZE STEP
        if self.status == StatusPoint.running:
            self.analyze_step()

        # PLOTTING STEP
        if self.status == StatusPoint.analyze:
            self.plotting_step()

        # Done with calibration? exit the loop
        if self.finished():
            return

        # NEXT STEP
        if self.status == StatusPoint.plot:
            self.next_step()

    def starting_step(self):
        self.status = StatusPoint.iteration_start

        # Restart the time for each iteration
        self.iteration_start = datetime.now().replace(microsecond=0)
        logger.info('---- Starting Iteration %d ----' % self.iteration)

    def commission_step(self):
        # Ready for commissioning
        self.status = StatusPoint.commission

        # Get the params from the next_point
        next_params = self.next_point_algo.get_samples_for_iteration(self.iteration)
        self.set_samples_for_iteration(next_params, self.next_point_algo)

        # Then commission
        self.commission_iteration(next_params)

        # Call the plot for post commission plots
        self.plot_iteration()

    def analyze_step(self):
        # Ready for analyzing
        self.status = StatusPoint.analyze

        # Analyze the iteration
        self.analyze_iteration()

    def plotting_step(self):
        # Ready for plotting
        self.status = StatusPoint.plot

        # Plot the iteration
        self.plot_iteration()

    def next_step(self):
        # Ready for next point
        self.status = StatusPoint.next_point

        self.next_point_algo.update_iteration(self.iteration)
        self.set_next_point(self.next_point_algo)

    def commission_iteration(self, next_params):
        """
        Commission an experiment of simulations constructed from a list of combinations of
        random seeds, calibration sites, and the next sample points.
        Cache the relevant experiment and simulation information to the IterationState.
        """
        if self.simulations:
            logger.info('Reloading simulation data from cached iteration (%s) state.' % self.iteration)
            self.exp_manager = ExperimentManagerFactory.from_experiment(
                DataStore.get_experiment(self.experiment_id))
        else:
            self.exp_manager = ExperimentManagerFactory.from_setup()

            # use passed in function to create exp_builder
            exp_builder = self.exp_builder_func(next_params)

            self.exp_manager.run_simulations(
                config_builder=self.config_builder,
                exp_name='%s_iter%d' % (self.calibration_name, self.iteration),
                exp_builder=exp_builder,
                suite_id=self.suite_id)

            self.simulations = self.exp_manager.experiment.toJSON()['simulations']
            self.experiment_id = self.exp_manager.experiment.exp_id
            self.save()

    def plot_iteration(self):
        # Run all the plotters
        map(lambda plotter: plotter.visualize(self), self.plotters)
        gc.collect()

    def analyze_iteration(self):
        """
        Analyze the output of completed simulations by using the relevant analyzers by site.
        Cache the results that are returned by those analyzers.
        """
        if self.results:
            logger.info('Reloading results from cached iteration state.')
            return self.results['total']
        if self.exp_manager:
            exp_manager = self.exp_manager
        else:
            exp = retrieve_experiment(self.experiment_id, verbose=True)
            exp_manager = ExperimentManagerFactory.from_experiment(exp)

        analyzerManager = AnalyzeManager(exp_manager.experiment, self.analyzer_list, working_dir=self.iteration_directory)
        analyzerManager.analyze()

        # Ask the analyzers to cache themselves
        cached_analyses = {a.uid(): a.cache() for a in analyzerManager.analyzers}
        logger.debug(cached_analyses)

        # Get the results from the analyzers and ask the next point how it wants to cache them
        results = pd.DataFrame({a.uid(): a.result for a in analyzerManager.analyzers})
        cached_results = self.next_point_algo.get_results_to_cache(results)
        logger.debug(cached_results)

        # Store the analyzers and results in the iteration state
        self.analyzers = cached_analyses
        self.results = cached_results

        # Set those results in the next point algorithm
        self.next_point_algo.set_results_for_iteration(self.iteration, results)
        self.set_next_point(self.next_point_algo)

        # Update the summary table and all the results
        all_results, summary_table = self.next_point_algo.update_summary_table(self, self.all_results)
        self.all_results = all_results
        self.summary_table = summary_table
        logger.info(summary_table)

        # Cache IterationState
        self.save()

    def wait_for_finished(self, verbose=True, init_sleep=1.0, sleep_time=10):
        while True:
            time.sleep(init_sleep)

            # Output time info
            current_time = datetime.now()
            iteration_time_elapsed = current_time - self.iteration_start
            calibration_time_elapsed = current_time - self.calibration_start

            logger.info('\n\nCalibration: %s' % self.calibration_name)
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
                logger.error('Cannot get simulation status. Calibration cannot continue. Exiting...')
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

        # Refresh the experiment
        self.exp_manager.refresh_experiment()

        # Wait when we are all done to make sure all the output files have time to get written
        time.sleep(0.5)

    def kill(self):
        """
        Kill the current calibration
        """
        self.exp_manager.cancel_experiment()

        logger.info("Waiting to complete cancellation...")
        self.exp_manager.wait_for_finished(verbose=False, sleep_time=1)

        # Print confirmation
        logger.info("Calibration %s successfully cancelled!" % self.calibration_name)

    @property
    def iteration_directory(self):
        return os.path.join(self.calibration_name, 'iter%d' % self.iteration)

    @property
    def param_names(self):
        return self.next_point_algo.get_param_names()

    def finished(self):
        """ The next-point algorithm has reached its termination condition. """
        return self.next_point_algo.end_condition()

    def reset_state(self):
        self.samples_for_this_iteration = {}
        self.next_point = {}
        self.simulations = {}
        self.experiment_id = None
        self.analyzers = {}
        self.results = {}

    def reset_to_step(self, iter_step=None):
        last_state_by_step = [('commission', ('samples_for_this_iteration')),
                              ('analyze', ('simulations',)),
                              ('next_point', ('results', 'analyzers'))]

        for step, states in reversed(last_state_by_step):
            if step == iter_step:  # remove cached states back to desired resumption point
                break
            logger.info('Clearing IterationState attribute(s): %s', states)
            for state in states:
                attr = getattr(self, state)
                if isinstance(attr, list):
                    attr[:] = []  # clear() only for dict before Python 3.3
                else:
                    attr.clear()

    @classmethod
    def from_file(cls, filepath):
        with open(filepath, 'r') as f:
            return cls(**json.load(f, object_hook=json_numpy_obj_hook))

    def to_file(self, filepath):
        state = {
                 'status': self.status.name,
                 'samples_for_this_iteration': self.samples_for_this_iteration,
                 'analyzers': self.analyzers,
                 'iteration': self.iteration,
                 'iteration_start': self.iteration_start,
                 'results': self.results,
                 'calibration_name': self.calibration_name,
                 'experiment_id': self.experiment_id,
                 'simulations': self.simulations,
                 'next_point': self.next_point,
                 'suite_id': self.suite_id
                }

        with open(filepath, 'w') as f:
            json.dump(state, f, indent=4, cls=NumpyEncoder)

    @classmethod
    def restore_state(cls, exp_name, iteration):
        """
        Restore IterationState
        """
        iter_directory = os.path.join(exp_name, 'iter%d' % iteration)
        iter_file = os.path.join(iter_directory, 'IterationState.json')
        return cls.from_file(iter_file)

    def set_samples_for_iteration(self, samples, next_point):
        if isinstance(samples, pd.DataFrame):
            dtypes = {name: str(data.dtype) for name, data in samples.iteritems()}
            self.samples_for_this_iteration_dtypes = dtypes
            samples_NaN_to_Null = samples.where(~samples.isnull(), other=None)
            self.samples_for_this_iteration = samples_NaN_to_Null.to_dict(orient='list')
        else:
            self.samples_for_this_iteration = samples

        # Also refresh the next point state
        self.set_next_point(next_point)

    # Always trigger a save when setting next_point
    def set_next_point(self, next_point):
        self.next_point = next_point.get_state()
        self.save()

    def save(self, backup_existing=False):
        """
        Cache information about the IterationState that is needed to resume after an interruption.
        If resuming from an existing iteration, also copy to backup the initial cached state.
        """
        try:
            os.makedirs(self.iteration_directory)
        except OSError:
            pass

        iter_state_path = os.path.join(self.iteration_directory, 'IterationState.json')
        if backup_existing and os.path.exists(iter_state_path):
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now().replace(microsecond=0)))
            os.rename(iter_state_path, os.path.join(self.iteration_directory, 'IterationState_%s.json' % backup_id))

        self.to_file(iter_state_path)
