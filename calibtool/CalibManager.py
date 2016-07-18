import glob
import json
import logging
import os
import pprint
import re
import shutil
import time
import pandas as pd
from datetime import datetime
from calibtool.plotters import SiteDataPlotter
from IterationState import IterationState
from simtools import utils
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder
from utils import NumpyEncoder

logger = logging.getLogger(__name__)


class SampleIndexWrapper(object):
    """
    Wrapper for a SimConfigBuilder-modifying function to add metadata
    on sample-point index when called in a iteration over sample points
    """

    def __init__(self, sample_point_fn):
        self.sample_point_fn = sample_point_fn

    def __call__(self, idx):
        def func(cb, *args, **kwargs):
            params_dict = self.sample_point_fn(cb, *args, **kwargs)
            params_dict.update(cb.set_param('__sample_index__', idx))
            return params_dict

        return func


class CalibManager(object):
    """
    Manages the creation, execution, and resumption of multi-iteration a calibration suite.
    Each iteration spawns a new ExperimentManager to configure and commission either local
    or HPC simulations for a set of random seeds, sample points, and site configurations.
    """

    def __init__(self, setup, config_builder, sample_point_fn, sites, next_point,
                 name='calib_test', iteration_state=IterationState(),
                 sim_runs_per_param_set=1, num_to_plot=10, max_iterations=5, plotters=list()):

        self.name = name
        self.setup = setup
        self.config_builder = config_builder
        self.sample_point_fn = SampleIndexWrapper(sample_point_fn)
        self.sites = sites
        self.next_point = next_point
        self.iteration_state = iteration_state
        self.sim_runs_per_param_set = sim_runs_per_param_set
        self.num_to_plot = num_to_plot
        self.max_iterations = max_iterations
        self.location = self.setup.get('type')
        self.suite_id = None
        self.all_results = None
        self.exp_manager = None
        self.plotters = plotters
        self.calibration_start = None
        self.iteration_start = None

    def run_calibration(self, **kwargs):
        """
        Create and run a complete multi-iteration calibration suite.
        """
        self.location = self.setup.get('type')
        if 'location' in kwargs:
            kwargs.pop('location')

        exp_manager = ExperimentManagerFactory.from_setup(self.setup, self.location, **kwargs)
        logger.info(type(exp_manager))
        # exit()


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
            sleep(0.5)
            print "Calibration with name %s already exists in current directory" % self.name
            var = ""
            while var.upper() not in ('R', 'B', 'C', 'P', 'A'):
                var = raw_input('Do you want to [R]esume, [B]ackup + run, [C]leanup + run, [P]lotter, [A]bort:  ')

            # Abort
            if var == 'A':
                exit()
            elif var == 'B':
                tstamp = re.sub('[ :.-]', '_', str(datetime.now()))
                shutil.move(self.name, "%s_backup_%s" % (self.name, tstamp))
                self.create_calibration(location)
            elif var == "C":
                self.cleanup()
                time.sleep(1)
                self.create_calibration(location)
            elif var == "R":
                self.resume_from_iteration(location=location, **kwargs)
            elif var == "P":
                self.replot_calibration(**kwargs)
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
        self.calibration_start = datetime.now().replace(microsecond=0)

        while self.iteration < self.max_iterations:

            # Restart the time for each iteration
            self.iteration_start = datetime.now().replace(microsecond=0)

            logger.info('---- Iteration %d ----', self.iteration)
            next_params = self.get_next_parameters()

            self.commission_iteration(next_params, **kwargs)

            results = self.analyze_iteration()

            self.update_next_point(results)
            if self.finished():
                break

            # Fix iteration issue in Calibration.json (reason: above self.finished() always returns False)
            if self.iteration + 1 < self.max_iterations:
                self.increment_iteration()
            else:
                break

        # Print the calibration finish time
        current_time = datetime.now()
        calibration_time_elapsed = current_time - self.calibration_start
        logger.info("Calibration done (took %s)" % utils.verbose_timedelta(calibration_time_elapsed))

        self.finalize_calibration()

    def get_next_parameters(self):
        """
        Query the next-point algorithm for the next set of sample points.
        """
        if self.iteration_state.parameters:
            logger.info('Reloading next set of sample points from cached iteration state.')
            next_params = self.iteration_state.parameters['values']
        else:
            next_params = self.next_point.get_next_samples()
            self.iteration_state.parameters = {'names': self.param_names(), 'values': next_params.tolist()}
            self.iteration_state.next_point = self.next_point.get_current_state()
            self.cache_iteration_state(backup_existing=True)
        return next_params

    def commission_iteration(self, next_params, **kwargs):
        """
        Commission an experiment of simulations constructed from a list of combinations of
        random seeds, calibration sites, and the next sample points.
        Cache the relevant experiment and simulation information to the IterationState.
        """

        if self.iteration_state.simulations:
            logger.info('Reloading simulation data from cached iteration state.')
            self.exp_manager = ExperimentManagerFactory.from_data(self.iteration_state.simulations)
        else:
            self.exp_manager = ExperimentManagerFactory.from_setup(self.setup, self.location, **kwargs)
            if not self.suite_id:
                self.generate_suite_id(self.exp_manager)

            exp_builder = ModBuilder.from_combos(
                [ModBuilder.ModFn(self.config_builder.__class__.set_param, 'Run_Number', i)
                 for i in range(self.sim_runs_per_param_set)],
                [ModBuilder.ModFn(site.setup_fn)
                 for site in self.sites],
                [ModBuilder.ModFn(self.sample_point_fn(idx), sample_point)
                 for idx, sample_point in enumerate(next_params)])

            self.exp_manager.run_simulations(
                config_builder=self.config_builder,
                exp_name='%s_iter%d' % (self.name, self.iteration),
                exp_builder=exp_builder,
                suite_id=self.suite_id)

            self.iteration_state.simulations = self.exp_manager.exp_data
            self.cache_iteration_state()

        self.wait_for_finished()

    def wait_for_finished(self, verbose=True, init_sleep=1.0, sleep_time = 3):
        while True:
            time.sleep(init_sleep)

            # Output time info
            current_time = datetime.now()
            iteration_time_elapsed = current_time - self.iteration_start
            calibration_time_elapsed = current_time - self.calibration_start

            logger.info('\n\nCalibration: %s' % self.name)
            logger.info('Calibration started: %s' % self.calibration_start)
            logger.info('Current iteration: Iteration %s' % self.iteration)
            logger.info('Current Iteration Started: %s', self.iteration_start)
            logger.info('Time since iteration started: %s' % utils.verbose_timedelta(iteration_time_elapsed))
            logger.info('Time since calibration started: %s\n' % utils.verbose_timedelta(calibration_time_elapsed))

            # Retrieve simulation status and messages
            states, msgs = self.exp_manager.get_simulation_status(reload=True)

            # Test if we are all done
            if self.exp_manager.status_finished(states):
                # Wait when we are all done to make sure all the output files have time to get written
                time.sleep(sleep_time)
                break
            else:
                if verbose:
                    self.exp_manager.print_status(states, msgs)
                time.sleep(sleep_time)

        # Print the status one more time
        iteration_time_elapsed = current_time - self.iteration_start
        logger.info("Iteration %s done (took %s)" % (self.iteration, utils.verbose_timedelta(iteration_time_elapsed)))
        self.exp_manager.print_status(states, msgs)


    def analyze_iteration(self):
        """
        Analyze the output of completed simulations by using the relevant analyzers by site.
        Cache the results that are returned by those analyzers.
        """

        if self.iteration_state.results:
            logger.info('Reloading results from cached iteration state.')
            return self.iteration_state.results['total']

        exp_data = self.iteration_state.simulations
        exp_manager = ExperimentManagerFactory.from_data(exp_data)
        for site in self.sites:
            for analyzer in site.analyzers:
                logger.debug(site, analyzer)
                exp_manager.add_analyzer(analyzer)
        exp_manager.analyze_simulations()

        cached_analyses = {a.uid(): a.cache() for a in exp_manager.analyzers}
        logger.debug(cached_analyses)

        results = pd.DataFrame({a.uid(): a.result for a in exp_manager.analyzers})
        results['total'] = results.sum(axis=1)

        logger.debug(results)
        cached_results = results.to_dict(orient='list')

        self.iteration_state.analyzers = cached_analyses
        self.iteration_state.results = cached_results
        self.cache_iteration_state()

        iteration_summary = self.iteration_state.summary_table()

        self.all_results = pd.concat((self.all_results, iteration_summary)).sort_values(by='total', ascending=False)
        logger.info(self.all_results[['iteration', 'total']].head(10))
        self.cache_calibration()

        # Run all the plotters
        map(lambda plotter: plotter.visualize(self), self.plotters)

        # Write the CSV
        self.write_LL_csv()

        return results.total.tolist()

    def update_next_point(self, results):
        """
        Pass the latest evaluated results back to the next-point algorithm,
        which will update its state to either truncate the calibration 
        or generate the next set of sample points.
        """
        self.next_point.update_results(results)
        self.next_point.update_state(self.iteration)

    def finished(self):
        """ The next-point algorithm has reached its truncation condition. """
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
        self.cache_calibration(final_samples=final_samples)

    def generate_suite_id(self, exp_manager):
        """
        Get a new Suite ID from the LOCAL/HPC ExperimentManager
        and cache to calibration with this updated info.
        """
        self.suite_id = exp_manager.create_suite(self.name)
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
                 'suite_id': self.suite_id,
                 'iteration': self.iteration,
                 'param_names': self.param_names(),
                 'sites': self.site_analyzer_names(),
                 'results': self.serialize_results(),
                 'setup_overlay_file':self.setup.setup_file,
                 'selected_block': self.setup.selected_block}
        state.update(kwargs)
        json.dump(state, open(os.path.join(self.name, 'CalibManager.json'), 'wb'), indent=4, cls=NumpyEncoder)

    def write_LL_csv(self):
        """
        Write the LL_summary.csv with what is in the CalibManager
        """
        # Deep copy all_results and pnames to not disturb the calibration
        import copy
        pnames = copy.deepcopy(self.param_names())
        all_results = self.all_results.copy(True)

        # Prepare the dictionary for rounding
        dictround = {}
        for p in pnames:
            dictround[p] = 8

        # Get the results DataFrame rounded and reset the index so we can conserve the sample column when merging
        results_df = all_results.round(dictround).reset_index(level=0)

        # Get the simIds
        sims = list()
        for simid, values in self.iteration_state.simulations["sims"].iteritems():
            values['id'] = simid
            sims.append(values)

        # Put the simulation info in a dataframe and round it
        siminfo_df = pd.DataFrame(sims)
        siminfo_df = siminfo_df.round(dictround).rename(columns={'id': 'outputs'})

        # Merge the info with the results to be able to have parameters -> simulations ids
        m = pd.merge(results_df, siminfo_df,
                     on=pnames,
                     indicator=True)

        # Group the results by parameters and transform the ids into an array
        grouped = m.groupby(by=pnames, sort=False)
        df = grouped['outputs'].aggregate(lambda x: tuple(x))

        # Get back a DataFrame from the GroupObject
        df = df.reset_index()

        # Merge back with the results
        results_df = pd.merge(df, results_df, on=pnames)

        # Retrieve the mapping between id - path
        if self.location == "HPC":
            from simtools.OutputParser import CompsDTKOutputParser
            sims_paths = CompsDTKOutputParser.createSimDirectoryMap(suite_id=self.suite_id, save=False)
        else :
            sims_paths = dict()

            sim_info = self.iteration_state.simulations
            base_path = os.path.join(sim_info['sim_root'], "%s_%s" % (sim_info['exp_name'], sim_info['exp_id']))

            for sim_id, sim in sim_info['sims'].iteritems():
                sims_paths[sim_id] = os.path.join(base_path, sim_id)

        # Transform the ids in actual paths
        def find_path(el):
            paths = list()
            for e in el:
                paths.append(sims_paths[e])
            return ",".join(paths)

        results_df['outputs'] = results_df['outputs'].apply(find_path)

        # Defines the column order
        col_order = ['iteration', 'sample', 'total']
        col_order.extend(results_df.keys()[len(pnames)+2:-2])   # The analyzers
        col_order.extend(pnames)
        col_order.extend(['outputs'])

        # Concatenate the current csv
        csv_path = os.path.join(self.name, 'LL_all.csv')
        if os.path.exists(csv_path):
            # We need to get the same column order from the csv that the results_df to append them correctly
            current = pd.read_csv(open(csv_path, 'r'))[col_order]
            results_df = results_df.append(current, ignore_index = True)

        # Write the csv
        csv = results_df.sort_values(by='total', ascending=True)[col_order].to_csv(header=True, index=False)
        with open(csv_path, 'w') as fp:
            fp.writelines(csv)

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
            backup_id = 'backup_' + re.sub('[ :.-]', '_', str(datetime.now()))
            os.rename(iter_state_path, os.path.join(iter_directory, 'IterationState_%s.json' % backup_id))

        self.iteration_state.to_file(iter_state_path)

    def serialize_results(self):
        """
        Prepare summary results for serialization.
        N.B. we cast also the sample index and iteration to int32
             to avoid a NumpyEncoder issue with np.int64
        """

        if not isinstance(self.all_results, pd.DataFrame):
            return None

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

        # zdu: after restore state, self.iteration_state.results is not None any more
        # last_iteration = iteration if not self.iteration_state.results else iteration - 1
        # Fix
        last_iteration = iteration

        self.all_results = self.all_results[self.all_results.iteration <= last_iteration]
        logger.info('Restored results from iteration %d', last_iteration)
        logger.debug(self.all_results)
        self.cache_calibration()

    def resume_from_iteration(self, iteration=None, iter_step=None, **kwargs):
        """
        Restart calibration from specified iteration (default=latest)
        and from the specified iter_step in each iteration:
           * commission -- commission a new iteration of simulations based on existing next_params
           * analyze -- calculate results for an existing iteration of simulations
           * next_point -- generate next sample points from an existing set of results
        """

        if not os.path.isdir(self.name):
            raise Exception('Unable to find existing calibration in directory: %s' % self.name)

        self.location = self.setup.get('type')

        calib_data = self.read_calib_data()
        self.suite_id = calib_data.get('suite_id')

        latest_iteration = calib_data.get('iteration')

        if iteration is None:
            iteration = latest_iteration
            logger.info('Resuming calibration from last iteration: %d' % iteration)
        else:
            if latest_iteration < iteration:
                logger.warning(
                    'Latest iteration (%d) is before resumption target (%d).' % (latest_iteration, iteration))
                iteration = latest_iteration
            logger.info('Resuming calibration from iteration %d' % iteration)

        iter_directory = os.path.join(self.name, 'iter%d' % iteration)
        self.iteration_state = self.retrieve_iteration_state(iter_directory)
        self.restore_results(calib_data.get('results'), iteration)
        if iter_step:
            self.iteration_state.reset_to_step(iter_step)
            self.cache_iteration_state(backup_existing=True)

        # TODO: If we attempt to resume, with re-commissioning,
        #       we will have to roll back next_point to previous iteration?
        #       Do we ever want to do this, or would we just re-select the
        #       next parameters from the previous iteration state?
        logger.info('Resuming NextPointAlgorithm from cached status.')
        logger.debug(pprint.pformat(self.iteration_state.next_point))
        self.next_point.set_current_state(self.iteration_state.next_point)

        self.run_iterations(**kwargs)

    def replot_calibration(self, **kwargs):
        """
        Cleanup the existing plots, then re-do the plottering
        """
        logger.info('Start Re-Plot Process!')

        # make sure data exists for plottering
        if not os.path.isdir(self.name):
            raise Exception('Unable to find existing calibration in directory: %s' % self.name)

        self.replot_calibration_for_iteration(**kwargs)

    def replot_calibration_for_iteration(self, **kwargs):
        """
        start iteration loop
        for each existing iteration, results all_results
        """

        # restore the existing calibration data
        calib_data = self.read_calib_data()

        # restore calibration results
        results = calib_data.get('results')

        latest_iteration = calib_data.get('iteration')
        logger.info('latest_iteration = %s' % latest_iteration)

        # before iteration loop
        self.all_results = None

        # consider delete-only plot option
        delete_only = kwargs.get('delete') == 'DELETE'

        # re-do plottering for each of the iterations
        for i in range(0, latest_iteration + 1):
            logger.info('Re-plottering for iteration: %d' % i)

            # restore current iteration state
            iter_directory = os.path.join(self.name, 'iter%d' % i)
            self.iteration_state = self.retrieve_iteration_state(iter_directory)

            # restore all_results for current iteration
            self.restore_results_for_replot(results, i)

            # cleanup the existing plots of the current iteration before generate new plots
            map(lambda plotter: plotter.cleanup_plot(self), self.plotters)

            # consider the delete-only option
            if not delete_only:
                self.replot_for_iteration(i, latest_iteration)

    def replot_for_iteration(self, iteration, latest_iteration):
        """
        for the iteration given,
        re-plot and avoid duplicated re-plot
        """
        for plotter in self.plotters:
            case1 = not isinstance(plotter, SiteDataPlotter.SiteDataPlotter)
            case2 = isinstance(plotter, SiteDataPlotter.SiteDataPlotter) and iteration == latest_iteration
            if case1 or case2:
                plotter.visualize(self)

    def restore_results_for_replot(self, results, iteration):
        """
        Restore summary results from serialized state.
        """

        if not results:
            logger.info('No iteration cached results to reload from CalibManager.')
            return

        # restore results as DataFrame
        self.all_results = pd.DataFrame.from_dict(results, orient='columns')

        # finally restore all_results for current iteration
        self.all_results = self.all_results[self.all_results.iteration <= iteration]

    def kill(self):
        """
        Kill the current calibration
        """
        # Find the latest iteration
        iterations = glob.glob(os.path.join(self.name, "iter*"))
        latest_iteration = iterations[-1]

        # Load it
        it = IterationState.from_file(os.path.join(latest_iteration, 'IterationState.json'))

        # Retrieve the experiment manager and cancel all
        exp_manager = ExperimentManagerFactory.from_data(it.simulations)

        if self.location == "LOCAL":
            # LOCAL calibration
            exp_manager.cancel_simulations(killall=True)
        else:
            exp_manager.cancel_all_simulations()

        # Print confirmation
        print "Calibration %s successfully cancelled!" % self.name

    def cleanup(self):
        """
        Cleanup the current calibration
        - Delete the result directory
        - If LOCAL -> also delete the simulations
        """
        if self.location == 'LOCAL':
            calib_data = self.read_calib_data()
            iter_count = calib_data.get('iteration')
            # Delete the simulations too
            logger.info('Deleting local simulations')
            for i in range(0, iter_count):
                # Get the iteration state
                it = IterationState.from_file(os.path.join(self.name, 'iter%d' % i, 'IterationState.json'))
                # Extract the path where the simulations are stored
                sim_path = os.path.join(it.simulations['sim_root'],
                                        "%s_%s" % (it.simulations['exp_name'], it.simulations['exp_id']))
                # If exist -> delete
                if os.path.exists(sim_path):
                    try:
                        shutil.rmtree(sim_path)
                    except OSError:
                        logger.error("Failed to delete %s" % sim_path)

                # If the json exist too -> delete
                json_path = os.path.join('simulations',
                                         '%s_%s.json' % (it.simulations['exp_name'], it.simulations['exp_id']))
                if os.path.exists(json_path):
                    try:
                        os.remove(json_path)
                    except OSError:
                        logger.error("Failed to delete %s" % json_path)

        # Then delete the whole directory
        calib_dir = os.path.abspath(self.name)
        if os.path.exists(calib_dir):
            try:
                shutil.rmtree(calib_dir)
            except OSError:
                logger.error("Failed to delete %s" % calib_dir)

    def reanalyze(self):
        """
        Reanalyze the current calibration
        """
        calib_data = self.read_calib_data()

        if calib_data['location'] == 'HPC':
            utils.COMPS_login(self.setup.get('server_endpoint'))

        # Cleanup the LL_all.csv
        if os.path.exists(os.path.join(self.name, 'LL_all.csv')):
            os.remove(os.path.join(self.name, 'LL_all.csv'))

        # Get the count of iterations and save the suite_id
        iter_count = calib_data.get('iteration')
        suite_id = calib_data.get('suite_id')

        # Go through each already ran iterations
        for i in range(0, iter_count+1):
            # Create the path for the iteration dir
            iter_directory = os.path.join(self.name, 'iter%d' % i)

            # Create the state for the current iteration
            self.iteration_state = self.retrieve_iteration_state(iter_directory)
            self.iteration_state.iteration = i

            # Empty the results and analyzers
            self.iteration_state.results = {}
            self.iteration_state.analyzers = {}

            # Analyze again!
            res = self.analyze_iteration()

            # update next point
            self.update_next_point(res)

        # Before leaving -> increase the iteration / set back the suite_id
        self.iteration_state.iteration += 1
        self.suite_id = suite_id
        self.location = calib_data['location']

        # Also finalize
        self.finalize_calibration()

    def read_calib_data(self, force=False):
        try:
            return json.load(open(os.path.join(self.name, 'CalibManager.json'), 'rb'))
        except IOError:
            if not force:
                raise Exception('Unable to find metadata in %s/CalibManager.json' % self.name)
            else:
                return None


    @property
    def iteration(self):
        return self.iteration_state.iteration

    def iteration_directory(self):
        return os.path.join(self.name, 'iter%d' % self.iteration)

    def state_for_iteration(self, iteration):
        iter_directory = os.path.join(self.name, 'iter%d' % iteration)
        return IterationState.from_file(os.path.join(iter_directory, 'IterationState.json'))

    def param_names(self):
        return self.next_point.prior_fn.params

    def site_analyzer_names(self):
        return {site.name: [a.name for a in site.analyzers] for site in self.sites}
