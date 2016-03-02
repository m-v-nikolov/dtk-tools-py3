import logging

import numpy as np

logger = logging.getLogger(__name__)


class NextPointAlgorithm(object):
    '''
    The algorithm that chooses a next set of sample points
    based on the results of analyses on previous iterations.
    '''

    def __init__(self, prior_fn,
                 initial_samples=1e4,
                 samples_per_iteration=1e3,
                 current_state={}):

        self.prior_fn = prior_fn
        self.samples_per_iteration = int(samples_per_iteration)
        self.set_current_state(current_state)
        if self.samples.size == 0:
            self.set_initial_samples(initial_samples)

        self.iteration = 0
        self.max_resampling_attempts = 100
        self.n_dimensions = self.samples[0].size

        logger.info('%s instance with %d initial %d-dimensional samples and %d per iteration',
                    self.__class__.__name__, self.samples.shape[0], 
                    self.n_dimensions, self.samples_per_iteration)

    def set_current_state(self, state):
        '''
        Initialize the current state of the next-point algorithm,
        either to the default of initially empty lists of sample points,
        or to a de-serialized state passed according to the 'state' argument.

        Also initialize the lists of 'results' and 'priors' by sample point.
        '''

        self.samples = state.get('samples', np.array([]))
        self.latest_samples = state.get('latest_samples', np.array([]))

        if (self.samples.size > 0) ^ (self.latest_samples.size > 0):
            raise Exception('Both samples (size=%d) and latest_samples (size=%d) '
                            'should be empty or already initialized.',
                            self.samples.size, self.latest_samples.size)

        self.results = state.get('results', [])
        self.priors = state.get('priors', [])

    def set_initial_samples(self, initial_samples):
        '''
        Set the initial samples points for the NextPointAlgorithm.
        If initial_samples parameter is an array, use those values as initial samples.
        Otherwise, if initial_samples parameter is a number,
        draw the specified number randomly from the prior distribution.
        '''

        if isinstance(initial_samples, (int, float)):  # allow float like 1e3
            self.samples = self.sample_from_function(self.prior_fn, int(initial_samples))
        elif isinstance(initial_samples, (list, np.ndarray)):
            self.samples = np.array(initial_samples)
        else:
            raise Exception("The 'initial_samples' parameter must be a number or an array.")

        logger.debug('Initial samples:\n%s' % self.samples)
        self.latest_samples = self.samples[:]

    def update_results(self, results):
        '''
        For an iteration manager to pass back the results of analyses
        on simulations by sample point to the next-point algorithm,
        for example the log-likelihoods of a calibration suite.
        '''

        self.results.extend(results)
        logger.debug('Results:\n%s', self.results)

    def update_state(self, iteration):
        '''
        Update the next-point algorithm state and select next samples.
        '''

        self.update_iteration(iteration)
        self.update_samples()

    def update_iteration(self, iteration):
        '''
        Update the current iteration state of the algorithm.
        '''

        self.iteration = iteration
        logger.info('Updating %s at iteration %d:', self.__class__.__name__, iteration)

        self.priors.extend(self.prior_fn.pdf(self.latest_samples))
        logger.debug('Priors:\n%s', self.priors)

    def update_samples(self):
        '''
        Choose the next samples and concatenate to list of all samples,
        verifying that all samples are in regions with non-zero prior probability.
        '''

        next_samples = self.sample_from_function(
            self.next_point_fn(), self.samples_per_iteration)

        self.latest_samples = self.verify_valid_samples(next_samples)
        logger.debug('Next samples:\n%s', self.latest_samples)

        self.samples = np.concatenate((self.samples, self.latest_samples))
        logger.debug('All samples:\n%s', self.samples)

    def end_condition(self):
        '''
        Return a Boolean whether the next-point algorithm has reached its truncation condition.
        '''

        logger.info('Continuing NextPointAlgorithm iterations...')
        return False

    def get_next_samples(self):
        return self.latest_samples

    def get_final_samples(self):
        return dict(samples=self.samples)

    def get_current_state(self):
        return dict(samples=self.samples, 
                    latest_samples=self.latest_samples,
                    priors=self.priors,
                    results=self.results)

    def next_point_fn(self):
        ''' The base implementation will resample from the prior function. '''
        return self.prior_fn

    def verify_valid_samples(self, next_samples):
        '''
        Resample from next-point function until all samples have non-zero prior.
        '''

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

    @staticmethod
    def sample_from_function(function, N):
        return np.array([function.rvs() for i in range(N)])