import logging

import numpy as np
import pandas as pd
from scipy.stats import multivariate_normal
from scipy.spatial.distance import seuclidean

from calibtool.algorithms.NextPointAlgorithm import NextPointAlgorithm

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class IMIS(NextPointAlgorithm):
    """
    IMIS (Incremental Mixture Importance Sampling)

    Algorithm ported from R code:
    http://cran.r-project.org/web/packages/IMIS

    Full description from Adrian Raftery and Le Bao (2009):
    http://www.stat.washington.edu/research/reports/2009/tr560.pdf

    The basic idea of IMIS is that points with high importance weights are in areas where
    the target density is underrepresented by the importance sampling distribution. At each
    iteration, a multivariate normal distribution centered at the point with the highest importance
    weight is added to the current importance sampling distribution, which thus becomes
    a mixture of such functions and of the prior. In this way underrepresented parts of the
    parameter space are successively identified and are given representation, ending up with an
    iteratively constructed importance sampling distribution that covers the target distribution
    well.
    """

    def __init__(self, prior_fn, initial_samples=1e4, samples_per_iteration=1e3, n_resamples=3e3, current_state=None):

        super(IMIS, self).__init__()
        self.iteration = 0
        self.prior_fn = prior_fn
        self.samples_per_iteration = int(samples_per_iteration)
        self.initial_samples = initial_samples

        self.priors = []
        self.results = []
        self.samples = np.array([])
        self.latest_samples = np.array([])
        self.data = pd.DataFrame(
            columns=[['Iteration', '__sample_index__', 'Prior', 'Result'] + self.get_param_names()])

        self.set_state(current_state or {}, self.iteration)

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

        self.gaussian_probs = {}
        self.gaussian_centers = []
        self.gaussian_covariances = []

        self.n_resamples = n_resamples

        self.D = 1  # mixture of D multivariate normal distributions (optimization stage not implemented)
        self.weights = []

        self.validate_parameters()

    def validate_parameters(self):
        """
        Ensure valid parameter ranges: 'samples_per_iteration' is used to select N-closest points
        to maximum-weight sample, so it can't exceed 'n_initial_samples'.  It is also used to estimate
        weighted covariance, so it cannot be smaller than the dimensionality of the samples.
        """

        if self.samples_per_iteration > self.n_initial_samples:
            raise Exception('samples_per_iteration (%d) cannot exceed n_initial_samples (%d)'
                            % (self.samples_per_iteration, self.n_initial_samples))

        if self.samples_per_iteration <= self.n_dimensions:
            raise Exception('n_dimensions (%d) cannot exceed samples_per_iteration (%d)'
                            % (self.n_dimensions, self.samples_per_iteration))

    def choose_initial_samples(self):
        self.set_initial_samples()
        return self.get_next_samples_for_iteration(0)

    def set_initial_samples(self):
        """
        Set the initial samples points for the algorithm.
        If initial_samples parameter is an array, use those values as initial samples.
        Otherwise, if initial_samples parameter is a number,
        draw the specified number randomly from the prior distribution.
        """
        iteration = 0

        self.data = pd.DataFrame(
            columns=[['Iteration', '__sample_index__', 'Prior', 'Result'] + self.get_param_names()])
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

        self.n_initial_samples = self.samples.shape[0]
        self.prior_covariance = np.cov(self.samples.T)
        logger.debug('Covariance of prior samples:\n%s' % self.prior_covariance)

    def add_samples(self, samples, iteration):
        samples_df = pd.DataFrame(samples, columns=self.get_param_names())
        samples_df.index.name = '__sample_index__'
        samples_df['Iteration'] = iteration
        samples_df.reset_index(inplace=True)

        self.data = pd.concat([self.data, samples_df])

        logger.debug('__sample_index__:\n%s' % samples_df[self.get_param_names()].values)

    def get_next_samples_for_iteration(self, iteration):
        return self.data.query('Iteration == @iteration').sort_values('__sample_index__')[self.get_param_names()]

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

    def get_samples_for_iteration(self, iteration):
        # Note: this method is called only from commission stage.
        # Important to know this for resume feature (need to restore correct next_point including samples)
        if iteration == 0:
            samples = self.choose_initial_samples()
        else:
            samples = self.choose_next_point_samples(iteration)
            self.update_gaussian_probabilities(iteration - 1)
        samples.reset_index(drop=True, inplace=True)
        return self.generate_samples_from_df(samples)

    def update_iteration(self, iteration):
        """
        Initial Stage (iteration: k = 0)
            (a) Sample N inputs \theta_1, \theta_2, ... , \theta_N from the prior distribution p(\theta).

            (b) For each \theta_i, calculate the likelihood L_i, and form the importance weights:
                    w^(0)_i = L_i / sum(L_j).

        Importance Sampling Stage (iteration: k > 0; samples_per_iteration: B)
            (c) Calculate the likelihood of the new inputs and combine the new inputs with the
                previous ones. Form the importance weights:
                    w^(k)_i = c * L_i * p(\theta_i) / q^(k)(\theta_i),
                where c is chosen so that the weights add to 1, q(k) is the mixture sampling distribution:
                    q^(k) = (N_0/N_k) * p + (B/N_k) * sum(H_s)
                where H_s is the s-th multivariate normal distribution,
                and N_k = N_0 + B_k is the total number of inputs up to iteration k.
        """

        super(IMIS, self).update_iteration(iteration)

        if not self.iteration:
            sampling_envelope = self.priors
        else:
            w = float(self.n_initial_samples) / self.samples_per_iteration
            stack = np.vstack([[np.multiply(self.priors, w)], self.gaussian_probs])
            logger.debug('Stack weighted prior + gaussian sample prob %s:\n%s', stack.shape, stack)
            norm = (w + self.D + (self.iteration - 2))
            sampling_envelope = np.sum(stack, 0) / norm

        logger.debug('Sampling envelope:\n%s', sampling_envelope)

        self.weights = [p * l / e for (p, l, e) in
                        zip(self.priors, self.results, sampling_envelope)]  # TODO: perform in log space
        self.weights /= np.sum(self.weights)
        logger.debug('Weights:\n%s', self.weights)

    def update_state(self, iteration):
        """
        Update the next-point algorithm state and select next samples.
        """

        self.update_iteration(iteration)
        self.update_gaussian()

    def update_gaussian(self):
        """
        Importance Sampling Stage (iteration: k > 0; samples_per_iteration: B)

            (a) Choose the current maximum weight input as the center \theta^(k). Estimate \Sigma^(k) from
                the weighted covariance of the B inputs with the smallest Mahalanobis distances
                to \theta^(k), where the distances are calculated with respect to the covariance of the
                prior distribution and the weights are taken to be proportional to the average of
                the importance weights and 1/N_k.

            (b) Sample 'samples_per_iteration' new inputs from a multivariate Gaussian distribution
                H_k with covariance matrix \Sigma^(k).
        """

        self.update_gaussian_center()
        distances = self.weighted_distances_from_center()
        self.update_gaussian_covariance(distances)

    def update_gaussian_center(self):
        """
        Choose the current maximum weight input as the center point
        for the next iteration of multivariate-normal sampling.
        """

        max_weight_idx = np.argmax(self.weights)
        max_weight_sample = self.samples[max_weight_idx]
        logger.debug('Centering new points at:\n%s', max_weight_sample)
        self.gaussian_centers.append(max_weight_sample)

    def weighted_distances_from_center(self):
        """
        Calculate the covariance-weighted distances from the current maximum-weight sample.
        N.B. Using normalized Euclid instead of Mahalanobis if we're just going to diagonalize anyways.
        """

        max_weight_sample = self.gaussian_centers[-1]
        V = self.prior_covariance if self.prior_covariance.size == 1 else np.diag(self.prior_covariance)
        distances = [seuclidean(s, max_weight_sample, V=V) for s in self.samples]
        logger.debug('Distances:\n%s', distances)

        return distances

    def update_gaussian_covariance(self, distances):
        """
        Calculate the covariance of the next-iteration of multivariate-normal sampling
        from the "samples_per_iteration" closest samples.
        """

        n_closest_idxs = np.argsort(distances)[:self.samples_per_iteration]

        n_closest_weights = self.weights[n_closest_idxs]
        logger.debug('N-closest weights:\n%s', n_closest_weights)

        n_closest_samples = self.samples[n_closest_idxs]
        logger.debug('N-closest samples:\n%s', n_closest_samples)

        weighted_covariance = self.calculate_weighted_covariance(
            samples=n_closest_samples,
            weights=n_closest_weights + 1. / len(self.weights),
            center=self.gaussian_centers[-1])

        self.gaussian_covariances.append(weighted_covariance)

    def get_param_names(self):
        return list(self.prior_fn.params)

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

    def next_point_fn(self):
        """ IMIS next-point sampling from multivariate normal centered on the maximum weight. """
        return multivariate_normal(mean=self.gaussian_centers[-1], cov=self.gaussian_covariances[-1])

    def update_gaussian_probabilities(self, iteration):
        """
        Calculate the probabilities of all sample points as estimated from the
        multivariate-normal probability distribution function centered on the maximum weight
        and with covariance fitted from the most recent iteration.
        """

        if not iteration:
            self.gaussian_probs = multivariate_normal.pdf(
                self.samples, self.gaussian_centers[-1],
                self.gaussian_covariances[-1]).reshape((1, len(self.samples)))
        else:
            updated_gaussian_probs = np.zeros(((self.D + self.iteration), len(self.samples)))
            updated_gaussian_probs[:self.gaussian_probs.shape[0], :self.gaussian_probs.shape[1]] = self.gaussian_probs
            for j in range(iteration):
                updated_gaussian_probs[j, self.gaussian_probs.shape[1]:] = multivariate_normal.pdf(
                    self.latest_samples, self.gaussian_centers[j], self.gaussian_covariances[j])
            updated_gaussian_probs[-1:] = multivariate_normal.pdf(
                self.samples, self.gaussian_centers[-1], self.gaussian_covariances[-1])
            self.gaussian_probs = updated_gaussian_probs

        logger.debug('Gaussian sample probabilities %s:\n%s', self.gaussian_probs.shape, self.gaussian_probs)

    def calculate_weighted_covariance(self, samples, weights, center):
        """
        A weighted covariance of sample points.
        N.B. The weights are normalized as in the R function "cov.wt"
        """

        d = (samples - center)
        logger.debug('Directed distance of samples from center:\n%s', d)

        # if self.n_dimensions == 1:
        #     w = weights / sum(weights)
        #     logger.debug('Normalized weights:\n%s', w)
        #     logger.debug('Squared-distance of samples:\n%s', np.square(d))
        #     d2 = np.square(d)
        #     sig2 = np.dot(d2, w)
        # else:
        weights = weights / sum(weights)
        w = 1. / (1 - sum(np.square(weights)))
        wd = np.multiply(d.T, weights).T
        sig2 = w * np.dot(wd.T, d)

        logger.debug('Weighted covariance:\n%s', sig2)

        return sig2

    def end_condition(self):
        """
        Stopping Criterion:
            The algorithm ends when the importance sampling weights are reasonably uniform.
            Specifically, we end the algorithm when the expected fraction of unique points in the resample
            is at least (1 - 1/e) = 0.632. This is the expected fraction when the importance
            sampling weights are all equal, which is the case when the importance sampling function is
            the same as the target distribution.
        """

        weight_distribution = np.sum(1 - (1 - np.array(self.weights)) ** self.n_resamples)
        end_condition = (1 - np.exp(-1)) * self.n_resamples

        if weight_distribution > end_condition:
            logger.info('Truncating IMIS iteration: %0.2f > %0.2f', weight_distribution, end_condition)
            return True
        else:
            logger.info('Continuing IMIS iterations: %0.2f < %0.2f', weight_distribution, end_condition)
            return False

    def get_final_samples(self):
        nonzero_idxs = self.weights > 0
        idxs = [i for i, w in enumerate(self.weights[nonzero_idxs])]
        try:
            # Renormalize (disabled for now)
            probs = self.weights[nonzero_idxs]
            # probs /= probs.sum()

            resample_idxs = np.random.choice(idxs, self.n_resamples, replace=True, p=probs)
        except ValueError:
            # To isolate dtk-tools issue #96
            print(nonzero_idxs)
            print(self.weights)
            print(idxs)
            raise

        # Add the parameters
        params = self.get_param_names()
        ret = dict()
        for i in range(len(params)):
            ret[params[i]] = [param_values[i] for param_values in self.samples[resample_idxs]]

        # And the weights
        ret['weights'] = [val for val in self.weights[resample_idxs]]

        return {'final_samples': ret}

    def get_state(self):
        imis_state = dict(n_initial_samples=self.n_initial_samples,
                          data=self.prep_for_dict(self.data),
                          data_dtypes={name: str(data.dtype) for name, data in self.data.iteritems()},
                          gaussian_probs=self.gaussian_probs,
                          gaussian_centers=self.gaussian_centers,
                          gaussian_covariances=self.gaussian_covariances)
        return imis_state

    def set_state(self, state, iteration):
        data_dtypes = state.get('data_dtypes', [])
        if data_dtypes:
            self.data = pd.DataFrame.from_dict(state['data'], orient='columns')
            self.latest_samples = pd.DataFrame.from_dict(state['data'], orient='columns')
            for c in self.data.columns:  # Argh
                self.data[c] = self.data[c].astype(data_dtypes[c])

        self.n_initial_samples = state.get('n_initial_samples', 0)
        self.gaussian_probs = state.get('gaussian_probs', {})
        self.gaussian_centers = state.get('gaussian_centers', [])
        self.gaussian_covariances = state.get('gaussian_covariances', [])

        if state:
            self.validate_parameters()  # if the current state is being reset from file

    def set_results_for_iteration(self, iteration, results):
        results = results.total.tolist()
        logger.info('%s: Choosing samples at iteration %d:', self.__class__.__name__, iteration)
        logger.debug('Results:\n%s', results)

        # update self.data first
        data_by_iter = self.data.set_index('Iteration')
        if iteration + 1 in data_by_iter.index.unique():
            # Been here before, reset
            data_by_iter = data_by_iter.loc[:iteration]

        # Store results ... even if changed
        data_by_iter.loc[iteration, 'Result'] = results
        data_by_iter.loc[iteration, 'Prior'] = self.prior_fn.pdf(self.latest_samples)
        self.data = data_by_iter.reset_index()

        # make two properties available which will be used in the following steps: self.update_state
        self.priors = list(data_by_iter['Prior'])
        self.results = list(data_by_iter['Result'])
        self.update_state(iteration)

    def cleanup(self):
        self.gaussian_probs = {}
        self.gaussian_covariances = []
        self.gaussian_centers = []

    def restore(self, iteration_state):
        self.gaussian_covariances = iteration_state.next_point['gaussian_covariances']
        self.gaussian_centers = iteration_state.next_point['gaussian_centers']
