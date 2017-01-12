import logging

import numpy as np
import pandas as pd

logger = logging.getLogger(__name__)


class NextPointAlgorithm(object):
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
            self.generate_variables_from_data(self.initial_samples)

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
        self.generate_variables_from_data(self.initial_samples)

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
        self.generate_variables_from_data(self.samples_per_iteration)

        logger.debug('Next samples:\n%s', self.latest_samples)

        return self.get_next_samples_for_iteration(iteration)

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

    def update_samples(self):
        pass

    def end_condition(self):
        """
        Return a Boolean whether the next-point algorithm has reached its truncation condition.
        """

        logger.info('Continuing NextPointAlgorithm iterations...')
        return False

    def get_next_samples(self):
        return self.latest_samples

    def get_final_samples_orig(self):
        return dict(samples=self.samples)

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

        # restore some properties from self.data
        samples_for_iteration = self.initial_samples if iteration == 0 else self.samples_per_iteration
        self.generate_variables_from_data(samples_for_iteration)

    def generate_variables_from_data(self, samples_number):
        """
        restore some properties from self.data
        """
        # keep as numpy.ndarray type
        self.samples = self.data[self.get_param_names()].values
        self.latest_samples = self.data.tail(samples_number)[self.get_param_names()].values

        if self.samples.size > 0:
            self.n_dimensions = self.samples[0].size

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