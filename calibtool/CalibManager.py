import copy
from datetime import datetime
import json
import logging
import os
import pprint
import re

import pandas as pd

from simtools.ExperimentManager import ExperimentManagerFactory
from simtools.ModBuilder import ModBuilder

from IterationState import IterationState
from visualize import LikelihoodPlotter, SiteDataPlotter

logger = logging.getLogger(__name__)


class SampleIndexWrapper(object):
    '''
    Wrapper for a SimConfigBuilder-modifying function to add metadata
    on sample-point index when called in a iteration over sample points
    '''

    def __init__(self, sample_point_fn):
        self.sample_point_fn = sample_point_fn

    def __call__(self, idx):
        def func(cb, *args, **kwargs):
            params_dict = self.sample_point_fn(cb, *args, **kwargs)
            params_dict.update(cb.set_param('__sample_index__', idx))
            return params_dict
        return func


class CalibManager(object):
    '''
    Manages the creation, execution, and resumption of multi-iteration a calibration suite.
    Each iteration spawns a new ExperimentManager to configure and commission either local
    or HPC simulations for a set of random seeds, sample points, and site configurations.
    '''

    def __init__(self, setup, config_builder, sample_point_fn, sites, next_point, 
                 name='calib_test', iteration_state=IterationState(), location='LOCAL',
                 sim_runs_per_param_set=1, num_to_plot=10, max_iterations=5):

        self.name = name
        self.setup = setup
        self.config_builder = config_builder
        self.sample_point_fn = SampleIndexWrapper(sample_point_fn)
        self.sites = sites
        self.next_point = next_point
        self.iteration_state = iteration_state

        self.location = location
        self.sim_runs_per_param_set = sim_runs_per_param_set
        self.num_to_plot = num_to_plot
        self.max_iterations = max_iterations

        self.suite_id = None
        self.all_results = None

    def run_calibration(self, **kwargs):
        '''
        Create and run a complete multi-iteration calibration suite.
        '''

        if 'location' in kwargs:
            self.location = kwargs.pop('location')

        self.create_calibration(self.location)
        self.run_iterations(**kwargs)

    def create_calibration(self, location):
        '''
        Create the working directory for a new calibration.
        Cache the relevant suite-level information to allow re-initializing this instance.
        '''

        try :
            os.mkdir(self.name)
            self.cache_calibration()
        except OSError :
            #logger.warning('Calibration with name %s already exists in current directory.', self.name)
            raise Exception('Calibration with name %s already exists in current directory. '
                            'Use resume_calibration to continue from a previous iteration.', self.name)

    def run_iterations(self, **kwargs):
        '''
        Run the iteration loop consisting of the following steps:
           * getting parameters to sample from next-point algorithm
             (based on results evaluated from previous iterations)
           * commissioning simulations corresponding to these samples
           * evaluating the results at each sample point by comparing
             the simulation output to appropriate reference data
           * updating the next-point algorithm with sample-point results
             and either truncating or generating next sample points.
        '''

        while self.iteration < self.max_iterations:
            logger.info('Iteration %d', self.iteration)
            next_params = self.get_next_parameters()

            self.commission_iteration(next_params, **kwargs)

            results = self.analyze_iteration()

            self.update_next_point(results)
            if self.finished():
                break
            self.increment_iteration()

        self.finalize_calibration()

    def get_next_parameters(self):
        '''
        Query the next-point algorithm for the next set of sample points.
        '''
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
        '''
        Commission an experiment of simulations constructed from a list of combinations of
        random seeds, calibration sites, and the next sample points.
        Cache the relevant experiment and simulation information to the IterationState.
        '''

        if self.iteration_state.simulations:
            logger.info('Reloading simulation data from cached iteration state.')
            exp_manager = ExperimentManagerFactory.from_data(self.iteration_state.simulations)
        else:
            exp_manager = ExperimentManagerFactory.from_setup(self.setup, self.location, **kwargs)
            if not self.suite_id:
                self.generate_suite_id(exp_manager)

            exp_builder = ModBuilder.from_combos(
                [ModBuilder.ModFn(self.config_builder.__class__.set_param, 'Run_Number', i)
                    for i in range(self.sim_runs_per_param_set)],
                [ModBuilder.ModFn(site.setup_fn)
                    for site in self.sites],
                [ModBuilder.ModFn(self.sample_point_fn(idx), sample_point)
                    for idx, sample_point in enumerate(next_params)])

            exp_manager.run_simulations(
                config_builder=self.config_builder,
                exp_name='%s_iter%d' % (self.name, self.iteration),
                exp_builder=exp_builder,
                suite_id=self.suite_id)

            self.iteration_state.simulations = exp_manager.exp_data
            self.cache_iteration_state()
            sim_ids = exp_manager.exp_data['sims'].keys()

        exp_manager.wait_for_finished(verbose=True, init_sleep=1.0)  # TODO: resolve status.txt line[-1] IndexError?

    def analyze_iteration(self):
        '''
        Analyze the output of completed simulations by using the relevant analyzers by site.
        Cache the results that are returned by those analyzers.
        '''

        if self.iteration_state.results:
            logger.info('Reloading results from cached iteration state.')
            return [sample['total'] for sample in self.iteration_state.results]

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

        # TODO: specify list of CalibPlotter instances in __init__
        #       to allow plotting to be configured appropriately for desired workflow?
        #       and/or re-plot from "calibtool plot commandline"?
        combine_sites = True
        plotters = [LikelihoodPlotter(self, combine_sites), SiteDataPlotter(self, combine_sites)]
        for plotter in plotters:
            plotter.visualize()

        return results.total.tolist()

    def update_next_point(self, results):
        '''
        Pass the latest evaluated results back to the next-point algorithm,
        which will update its state to either truncate the calibration 
        or generate the next set of sample points.
        '''
        self.next_point.update_results(results)
        self.next_point.update_state(self.iteration)

    def finished(self):
        ''' The next-point algorithm has reached its truncation condition. '''
        return self.next_point.end_condition()

    def increment_iteration(self):
        ''' Cache the last iteration state and initialize a new iteration. '''
        self.cache_iteration_state()
        self.iteration_state.increment_iteration()
        self.cache_calibration()  # to update latest iteration

    def finalize_calibration(self):
        ''' Get the final samples (and any associated information like weights) from algo. '''
        final_samples = self.next_point.get_final_samples()
        # TODO: write this out somewhere like cache_calibration?!

    def generate_suite_id(self, exp_manager):
        '''
        Get a new Suite ID from the LOCAL/HPC ExperimentManager
        and cache to calibration with this updated info.
        '''
        self.suite_id = exp_manager.create_suite(self.name)
        self.cache_calibration()

    def cache_calibration(self):
        '''
        Cache information about the CalibManager that is needed to resume after an interruption.
        N.B. This is not currently the complete state, some of which relies on nested and frozen functions.
             As such, the 'resume' logic relies on the existence of the original configuration script.
        '''

        # TODO: resolve un-picklable nested SetupFunctions.set_calibration_site for self.sites
        #       and frozen scipy.stats functions in MultiVariatePrior.function for self.next_point
        state = {'name': self.name,
                 'location': self.location,
                 'suite_id': self.suite_id,
                 'iteration': self.iteration,
                 'param_names': self.param_names(),
                 'sites': self.site_analyzer_names(),
                 'results': self.all_results.to_dict(orient='list') if isinstance(self.all_results, pd.DataFrame) else None}
        json.dump(state, open(os.path.join(self.name, 'CalibManager.json'), 'wb'), indent=4)

    def cache_iteration_state(self, backup_existing=False):
        '''
        Cache information about the IterationState that is needed to resume after an interruption.
        If resuming from an existing iteration, also copy to backup the initial cached state.
        '''
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

    def resume_from_iteration(self, iteration=None, iter_step=None, **kwargs):
        '''
        Restart calibration from specified iteration (default=latest)
        and from the specified iter_step in each iteration:
           * commission -- commission a new iteration of simulations based on existing next_params
           * analyze -- calculate results for an existing iteration of simulations
           * next_point -- generate next sample points from an existing set of results
        '''

        if not os.path.isdir(self.name):
            raise Exception('Unable to find existing calibration in directory: %s' % self.name)

        try:
            calib_data = json.load(open(os.path.join(self.name, 'CalibManager.json'), 'rb'))
        except IOError:
            raise Exception('Unable to find metadata in %s/CalibManager.json' % self.name)

        kw_location = kwargs.pop('location')
        self.location = calib_data.get('location', kw_location if kw_location else self.location)
        self.suite_id = calib_data.get('suite_id')
        latest_iteration = calib_data.get('iteration')

        if iteration == None:
            iteration = latest_iteration
            logger.info('Resuming calibration from last iteration: %d' % iteration)
        else:
            if latest_iteration < iteration:
                logger.warning('Latest iteration (%d) is before resumption target (%d).' % (latest_iteration, iteration))
                iteration = latest_iteration
            logger.info('Resuming calibration from iteration %d' % iteration)

        iter_directory = os.path.join(self.name, 'iter%d' % iteration)
        if not os.path.isdir(iter_directory):
            raise Exception('Unable to find calibration iteration in directory: %s' % iter_directory)

        try:
            self.iteration_state = IterationState.from_file(os.path.join(iter_directory, 'IterationState.json'))
            if iter_step:
                self.iteration_state.reset_to_step(iter_step)
                self.cache_iteration_state(backup_existing=True)
        except IOError:
            raise Exception('Unable to find metadata in %s/IterationState.json' % iter_directory)

        logger.info('Resuming NextPointAlgorithm from cached status.')
        logger.debug(pprint.pformat(self.iteration_state.next_point))
        self.next_point.set_current_state(self.iteration_state.next_point)

        self.run_iterations(**kwargs)

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