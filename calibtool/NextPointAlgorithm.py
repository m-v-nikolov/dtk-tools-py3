import logging

import numpy as np
import pandas as pd

from calibtool.algorithms.BaseNextPointAlgorithm import BaseNextPointAlgorithm

logger = logging.getLogger(__name__)


class NextPointAlgorithm(BaseNextPointAlgorithm):
    """
    The algorithm that chooses a next set of sample points
    based on the results of analyses on previous iterations.
    """

    def __init__(self, prior_fn,
                 initial_samples=1e4,
                 samples_per_iteration=1e3,
                 current_state={}):

        self.iteration = 0
        self.prior_fn = prior_fn
        self.samples_per_iteration = int(samples_per_iteration)
        self.initial_samples = initial_samples

        self.priors = []
        self.results = []
        self.samples = np.array([])
        self.latest_samples = np.array([])
        self.data = pd.DataFrame(columns=[['Iteration', '__sample_index__', 'Prior', 'Result'] + self.get_param_names()])

        self.set_state(current_state, self.iteration)

        if (self.samples.size > 0) ^ (self.latest_samples.size > 0):
            raise Exception('Both samples (size=%d) and latest_samples (size=%d) '
                            'should be empty or already initialized.',
                            self.samples.size, self.latest_samples.size)

        if self.samples.size == 0:
            self.set_initial_samples()
            self.generate_variables_from_data()

        self.max_resampling_attempts = 100
        self.n_dimensions = self.samples[0].size

        logger.info('%s instance with %d initial %d-dimensional samples and %d per iteration' %
                    (self.__class__.__name__, self.samples.shape[0],
                     self.n_dimensions, self.samples_per_iteration))

    def choose_initial_samples(self):
        self.set_initial_samples()
        return self.get_next_samples_for_iteration(0)

    def set_initial_samples(self):
        """
        Set the initial samples points for the NextPointAlgorithm.
        If initial_samples parameter is an array, use those values as initial samples.
        Otherwise, if initial_samples parameter is a number,
        draw the specified number randomly from the prior distribution.
        """
        iteration = 0

        self.data = pd.DataFrame(columns=[['Iteration', '__sample_index__', 'Prior', 'Result'] + self.get_param_names()])
        self.data['Iteration'] = self.data['Iteration'].astype(int)
        self.data['__sample_index__'] = self.data['__sample_index__'].astype(int)

        if isinstance(self.initial_samples, (int, float)):  # allow float like 1e3
            samples = self.sample_from_function(self.prior_fn, int(self.initial_samples))
        elif isinstance(self.initial_samples, (list, np.ndarray)):
            samples = np.array(self.initial_samples)
        else:
            raise Exception("The 'initial_samples' parameter must be a number or an array.")

        self.add_samples(samples, iteration)
        self.generate_variables_from_data()

        logger.debug('Initial samples:\n%s' % samples)

    def choose_next_point_samples(self, iteration):
        # Note: this is called from get_samples_for_iteration which is called only at commission stage
        #       therefore, this method is called also only at commission stage
        #       knowing this is very important for resume feature

        assert (iteration >= 1)

        next_samples = self.sample_from_function(
            self.next_point_fn(), self.samples_per_iteration)

        latest_samples = self.verify_valid_samples(next_samples)
        self.add_samples(latest_samples, iteration)
        self.generate_variables_from_data()

        logger.debug('Next samples:\n%s', self.latest_samples)

        return self.get_next_samples_for_iteration(iteration)

    def get_samples_for_iteration(self, iteration):
        # Note: this method is called only from commission stage.
        # Important to know this for resume feature (need to restore correct next_point including samples)
        if iteration == 0:
            samples = self.choose_initial_samples()
        else:
            samples = self.choose_next_point_samples(iteration)
            self.update_gaussian_probabilities(iteration - 1)

        return samples

    def add_samples(self, samples, iteration):
        samples_df = pd.DataFrame(samples, columns=self.get_param_names())
        samples_df.index.name = '__sample_index__'
        samples_df['Iteration'] = iteration
        samples_df.reset_index(inplace=True)

        self.data = pd.concat([self.data, samples_df])

        logger.debug('__sample_index__:\n%s' % samples_df[self.get_param_names()].values)

    def get_next_samples_for_iteration(self, iteration):
        return self.data.query('Iteration == @iteration').sort_values('__sample_index__')[self.get_param_names()]

    def update_results(self, results):
        pass

    def update_state(self, iteration):
        pass

    def update_iteration(self, iteration):
        """
        Update the current iteration state of the algorithm.
        """

        self.iteration = iteration
        logger.info('Updating %s at iteration %d:', self.__class__.__name__, iteration)

    def end_condition(self):
        """
        Return a Boolean whether the next-point algorithm has reached its truncation condition.
        """

        logger.info('Continuing NextPointAlgorithm iterations...')
        return False

    def get_next_samples(self):
        return self.latest_samples

    def get_final_samples(self):
        return dict(samples=self.samples)

    def get_state(self):
        return dict(
                    data=self.prep_for_dict(self.data),
                    data_dtypes={name: str(data.dtype) for name, data in self.data.iteritems()}
        )

    def prep_for_dict(self, df):
        return df.where(~df.isnull(), other=None).to_dict(orient='list')

    def set_state(self, state, iteration):
        data_dtypes = state.get('data_dtypes', [])
        if data_dtypes:
            self.data = pd.DataFrame.from_dict(state['data'], orient='columns')
            self.latest_samples = pd.DataFrame.from_dict(state['data'], orient='columns')
            for c in self.data.columns: # Argh
                self.data[c] = self.data[c].astype(data_dtypes[c])

        self.generate_variables_from_data()

    def generate_variables_from_data(self):
        """
        restore some properties from self.data
        """
        # keep as numpy.ndarray type
        self.samples = self.data[self.get_param_names()].values

        if self.samples.size > 0:
            data_by_iteration = self.data.set_index('Iteration')
            last_iter = sorted(data_by_iteration.index.unique())[-1]
            self.latest_samples = self.get_next_samples_for_iteration(last_iter).values

            self.n_dimensions = self.samples[0].size
        else:
            self.latest_samples = np.array([])

        # keep as list type
        self.priors = list(self.data['Prior'])
        self.results = list(self.data['Result'])

    def next_point_fn(self):
        """
        The base implementation will resample from the prior function.
        """
        return self.prior_fn

    def verify_valid_samples(self, next_samples):
        """
        Resample from next-point function until all samples have non-zero prior.
        """

        attempt = 0
        while attempt < self.max_resampling_attempts:
            sample_priors = self.prior_fn.pdf(next_samples)
            valid_samples = next_samples[sample_priors > 0]
            n_invalid = len(next_samples) - len(valid_samples)
            if not n_invalid:
                break
            logger.warning('Attempt %d: resampling to replace %d invalid samples '
                           'with non-positive prior probability.', attempt, n_invalid)
            resamples = self.sample_from_function(self.next_point_fn(), n_invalid)
            next_samples = np.concatenate((valid_samples, resamples))
            attempt += 1

        return next_samples

    def get_param_names(self):
        return self.prior_fn.params

    @staticmethod
    def sample_from_function(function, N):
        return np.array([function.rvs() for i in range(N)])

    def cleanup(self):
        pass

    def restore(self, iteration_state):
        pass

    def update_summary_table(self, iteration_state, previous_results):
        """
        Returns a summary table of the form:
          [result1 result2 results_total param1 param2 iteration simIds]
          index = sample
          Used by OptimTool and IMIS algorithm
        """
        results_df = pd.DataFrame.from_dict(iteration_state.results, orient='columns')
        results_df.index.name = 'sample'

        params_df = pd.DataFrame(iteration_state.samples_for_this_iteration)

        #for c in params_df.columns:  # Argh
        #    params_df[c] = params_df[c].astype(iteration_state.samples_for_this_iteration_dtypes[c])

        sims_df = pd.DataFrame.from_dict(iteration_state.simulations, orient='index')
        grouped = sims_df.groupby('__sample_index__', sort=True)
        simIds = tuple(group.index.values for sample, group in grouped)

        df = pd.concat((results_df, params_df), axis=1)
        df['iteration'] = iteration_state.iteration

        previous_results = pd.concat((previous_results, df)).sort_values(by='total', ascending=False)
        return previous_results, previous_results[['iteration', 'total']].head(10)

    def get_results_to_cache(self, results):
        results['total'] = results.sum(axis=1)
        return results.to_dict(orient='list')

    def generate_samples_from_df(self, dfsamples):
        # itertuples preserves datatype
        # First tuple element is index
        # Because parameter names are not necessarily valid python identifiers, have to build my own dictionary here
        samples = []
        for sample in dfsamples.itertuples():
            samples.append({k: v for k, v in zip(dfsamples.columns.values, sample[1:])})
        return samples
