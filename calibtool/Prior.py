import logging
from operator import mul

import numpy as np
import pandas as pd
import scipy.stats

logger = logging.getLogger(__name__)

# TODO: use SampleRange in LikelihoodPlotter ax.set_xlim


class SampleRange(object):

    """
    Container for min, max of a range and a type of sampling to use

    :param range_type: Type of sampling within range.  Supported values: linear, log, linear_int
    :param range_min: Minimum of sampling range.
    :param range_max: Maximum of sampling range.
    """

    def __init__(self, range_type, range_min, range_max):

        if range_max <= range_min:
            raise Exception('range_max (%f) must be greater than range_min (%f).' % (range_max, range_min))

        self.range_type = range_type
        self.range_min = range_min
        self.range_max = range_max
        self.function = self.get_sample_function()

    def get_sample_function(self):
        """
        Converts sample-range variables into scipy.stats frozen function
        :return: Frozen scipy.stats function
        """

        if self.range_type == 'linear':
            return scipy.stats.uniform(loc=self.range_min, scale=(self.range_max - self.range_min))
        elif self.range_type == 'log':
            if self.range_min <= 0:
                raise Exception('range_min (%f) must be greater than zero for range_type=log.' % self.range_min)
            return scipy.stats.reciprocal(a=self.range_min, b=self.range_max)
        elif self.range_type == 'linear_int':
            xx = range(int(self.range_min), int(self.range_max) + 1)
            ww = [1.0 / len(xx)] * len(xx)
            return scipy.stats.rv_discrete(name='linear_int', values=(xx, ww))
        else:
            raise Exception('Unknown range_type (%s). Supported types: linear, log, linear_int.' % self.range_type)

    def get_bins(self, n):
        if self.is_log():
            return np.logspace(np.log10(self.range_min), np.log10(self.range_max), n)
        else:
            return np.linspace(self.range_min, self.range_max, n)

    def is_log(self):
        return 'log' in self.range_type

    def is_int(self):
        return 'int' in self.range_type


class SampleFunctionContainer(object):

    """
    Container for a frozen function and optionally its associated sample-range properties
    """

    def __init__(self, function, sample_range=None):
        self.function = function
        self.sample_range = sample_range

    @classmethod
    def from_range(cls, sample_range):
        return cls(sample_range.function, sample_range)

    @classmethod
    def from_tuple(cls, *args):
        return cls.from_range(SampleRange(*args))

    def get_even_spaced_samples(self, n):
        """
        Returns an evenly spaced sampling of the percent-point function (inverse CDF)
        :param n: number of evenly spaced samples
        """
        return self.function.ppf(np.linspace(0.001, 0.999, n))

    def pdf(self, X):
        """
        Wrapper for contained function pdf with check for discrete distributions
        :return:
        """
        if isinstance(self.function, scipy.stats._distn_infrastructure.rv_frozen):
            return self.function.pdf(X)
        elif isinstance(self.function, scipy.stats._distn_infrastructure.rv_sample):
            if self.sample_range is not None and 'int' in self.sample_range.range_type:
                return self.function.pmf(np.round(X))  # round to NEAREST integer
            else:
                X_cdfs = self.function.cdf(X)
                X_rounded = self.function.ppf(X_cdfs)  # this will round down to value of non-zero PMF
                return self.function.pmf(X_rounded)
        else:
            raise Exception("Expecting a frozen scipy.stats function.")


class MultiVariatePrior(object):
    """
    Multi-variate wrapper exposing same interfaces
    as scipy.stats functions, i.e. pdf and rvs

    Different dimensions are drawn independently
    from the univariate distributions.

    : param sample_functions : list of scipy.stats frozen functions
    : param params : list of parameter names associated with functions (optional)
    : param ranges : list of SampleRange objects associated with functions (optional)
    : param name : name of MultiVariatePrior object (optional)
    """

    def __init__(self, functions, params=[], ranges=[], name=None):

        self.name = name

        if not params:
            params = range(len(functions))
        elif len(functions) != len(params):
            raise Exception("params and functions lists must have same length")

        if not ranges:
            ranges = [None] * len(functions)
        elif len(functions) != len(ranges):
            raise Exception("ranges and functions lists must have same length")

        self.sample_functions = {p: SampleFunctionContainer(f, r) for (p, f, r) in zip(params, functions, ranges)}

    @property
    def functions(self):
        return [sfc.function for sfc in self.sample_functions.values()]

    @property
    def params(self):
        return self.sample_functions.keys()

    @property
    def ndim(self):
        return len(self.functions)

    @classmethod
    def by_range(cls, **param_sample_ranges):
        """
        Builds multi-variate wrapper from keyword arguments of parameter names to SampleRange (min, max, type)

        :param param_sample_ranges: keyword arguments of parameter names to SampleRange tuple
        :return: MultiVariatePrior instance

        An example usage:

        > prior = MultiVariatePrior.by_range(
              MSP1_Merozoite_Kill_Fraction=('linear', 0.4, 0.7),
              Max_Individual_Infections=('linear_int', 3, 8),
              Base_Gametocyte_Production_Rate=('log', 0.001, 0.5))
        """

        ranges = [SampleRange(*sample_range_tuple) for sample_range_tuple in param_sample_ranges.values()]

        return cls(functions=[r.function for r in ranges], ranges=ranges, params=param_sample_ranges.keys())

    @classmethod
    def by_param(cls, **param_sample_functions):
        """
        Builds multi-variate wrapper from keyword arguments of parameter names to univariate frozen functions

        :param param_sample_functions: keyword arguments of parameter names to univariate object supporting pdf and rvs interfaces
        :return: MultiVariatePrior instance

        An example usage:

        > from scipy.stats import uniform
        > prior = MultiVariatePrior.by_param(
              MSP1_Merozoite_Kill_Fraction=uniform(loc=0.4, scale=0.3),  # from 0.4 to 0.7
              Nonspecific_Antigenicity_Factor=uniform(loc=0.1, scale=0.8))  # from 0.1 to 0.9
        """

        return cls(functions=param_sample_functions.values(), params=param_sample_functions.keys())

    def pdf(self, X):
        """
        Returns product of individual component function PDFs at each input point.
        : param X : array of points, where each point is an array of correct dimension.
        """

        if isinstance(X, list):
            X = np.array(X)  # allow equivalent python list or np.ndarray inputs

        if X.ndim == 2:
            npts, ndim = X.shape  # the default case
        elif X.ndim == 1:
            if len(self.functions) == 1:
                npts, ndim = X.size, 1  # multiple 1-d measurements: [1, 2, 3] --> [[1], [2], [3]]
            else:
                npts, ndim = 1, X.size  # a single multi-dimensional measurement: [1, 2, 3] --> [[1, 2, 3]]
            X = np.reshape(X, (npts, ndim))
        else:
            raise Exception('Expecting 1- or 2-dimensional array input.')

        if self.ndim == ndim:
            logger.debug('Input dimension = %d', ndim)
        else:
            raise Exception('Dimensionality of sample points (%d) does not match function (%d)' % (ndim, self.ndim))

        pdfs = []
        for params in X:
            pdfs.append(reduce(mul, [f.pdf(x) for f, x in zip(self.sample_functions.values(), params)], 1))
        return np.array(pdfs)

    def rvs(self, size=1):
        """
        Returns an array of random points, where each point is sampled randomly in its component dimensions.
        : param size : the number of random points to sample.
        """

        values = np.array([[f.rvs() for f in self.functions] for _ in range(size)]).squeeze()
        return values

    def lhs(self, size=1):
        """
        Returns a Latin Hypercube sample, drawn from the sampling ranges of the component dimensions
        :param size: the number of random points to sample
        """

        samples = np.zeros((size, len(self.functions)))
        for i, sample_function in enumerate(self.sample_functions.values()):
            sample_bins = sample_function.get_even_spaced_samples(size)
            np.random.shuffle(sample_bins)
            samples[:, i] = sample_bins

        return samples

    def to_dataframe(self, param_value_array):
        """
        Transforms an array of parameter-value arrays to a pandas.DataFrame with appropriate column names
        """
        return pd.DataFrame(data=param_value_array, columns=self.params)

    def to_dict(self, param_point):
        """
        Transforms an individual point in parameter space to a dictionary of parameter names to values.
        Also will round parameters where the range_type requires integer-only values.
        """
        int_param = [sfc.sample_range.is_int() if sfc.sample_range else False for sfc in self.sample_functions.values()]
        param_point = [int(np.round(p)) if i else p for p, i in zip(param_point, int_param)]
        return dict(zip(self.params, param_point))


if __name__ == '__main__':

    import matplotlib.pyplot as plt

    prior = MultiVariatePrior.by_range(
        MSP1_Merozoite_Kill_Fraction=('linear', 0.4, 0.7),
        Max_Individual_Infections=('linear_int', 3, 8),
        Base_Gametocyte_Production_Rate=('log', 0.001, 0.5))

    n_random = 5000
    n_bins = 50

    # Latin Hypercube sample and independent random variable samples
    dfs = [prior.to_dataframe(prior.lhs(size=n_random)),
           prior.to_dataframe(prior.rvs(size=n_random))]

    f, axs = plt.subplots(2, len(prior.params), figsize=(15, 8))
    for j, df in enumerate(dfs):
        for i, p in enumerate(prior.params):
            ax = axs[j][i]
            sample_range = prior.sample_functions[p].sample_range
            xscale = 'linear'
            if sample_range is None:
                stats = df[p].describe()
                vmin, vmax = stats.loc['min'], stats.loc['max']
                bins = np.linspace(stats.loc['min'], stats.loc['max'], n_bins)
            else:
                vmin, vmax = sample_range.range_min, sample_range.range_max
                bins = sample_range.get_bins(n_bins)
                if sample_range.is_log():
                    xscale = 'log'

            df[p].plot(kind='hist', ax=ax, bins=bins, alpha=0.5)
            ax.set(xscale=xscale, xlim=(vmin, vmax), title=p)

    f.set_tight_layout(True)

    plt.show()