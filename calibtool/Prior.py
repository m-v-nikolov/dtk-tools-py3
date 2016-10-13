import logging
from operator import mul

import numpy as np
import scipy.stats

logger = logging.getLogger(__name__)

'''
TODO:
- discrete distributions
- log-uniform, i.e. 10**uniform
- independent combinations of multi-variate normals
- Latin Hypercube Sampling?
'''

# TODO: fix unit tests


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

    @property
    def function(self):
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
            # TODO: make discrete
            return scipy.stats.uniform(loc=self.range_min, scale=(self.range_max - self.range_min))
        else:
            raise Exception('Unknown range_type (%s). Supported types: linear, log, linear_int.' % self.range_type)


class SampleFunction(object):

    """
    Container for a frozen function and optionally its associated sample-range properties
    """

    def __init__(self, function, sample_range=None):
        self.function = function
        self.sample_range = sample_range

    @classmethod
    def from_range(cls, sample_range):
        return cls(sample_range.function, sample_range)


class MultiVariatePrior(object):
    """
    Multi-variate wrapper exposing same interfaces
    as scipy.stats functions, i.e. pdf and rvs

    Different dimensions are drawn independently
    from the univariate distributions.

    : param sample_functions : dictionary of parameter names to SampleFunction containers
    """

    def __init__(self, sample_functions, name=None):
        self.sample_functions = sample_functions
        self.name = name

    @property
    def functions(self):
        return [sample_function.function for sample_function in self.sample_functions.values()]

    @property
    def params(self):
        return self.sample_functions.keys()

    @classmethod
    def by_range(cls, **param_sample_ranges):
        """
        Builds multi-variate wrapper from keyword arguments of parameter names to SampleRange (min, max, type)

        :param param_sample_ranges: keyword arguments of parameter names to SampleRange container
        :return: MultiVariatePrior instance

        An example usage:

        > prior = MultiVariatePrior.by_range(
              MSP1_Merozoite_Kill_Fraction=SampleRange('linear', 0.4, 0.7),
              Nonspecific_Antigenicity_Factor=SampleRange('linear', 0.1, 0.9),
              Base_Gametocyte_Production_Rate=SampleRange('log', 0.001, 0.5))
        """

        sample_functions = {param_name: SampleFunction.from_range(sample_range)
                            for param_name, sample_range in param_sample_ranges.items()}

        return cls(sample_functions)

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

        # TODO: adjust sample-point function in example_calibration.py to param dictionary

        sample_functions = {param_name: SampleFunction(sample_function)
                            for param_name, sample_function in param_sample_functions.items()}

        return cls(sample_functions)

    def pdf(self, X):
        """
        Returns product of individual component function PDFs at each input point.
        : param X : array of points, where each point is an array of correct dimension.
        """

        # TODO: should this function implicitly accept more input types? list, np.array, list(list), etc.

        input_dim = X.ndim if X.ndim == 1 else X.shape[1]

        if input_dim == 1:
            X = np.reshape(X, (X.shape[0], 1))

        if len(self.functions) == input_dim:
            logger.debug('Input dimension = %d', input_dim)
        else:
            raise Exception('Wrong shape')

        pdfs = []
        for params in X:
            pdfs.append(reduce(mul, [f.pdf(x) for f, x in zip(self.functions, params)], 1))
        return np.array(pdfs)

    def rvs(self, size=1):
        """
        Returns an array of random points, where each point is sampled randomly in its component dimensions.
        : param size : the number of random points to sample.
        """

        # TODO: assess whether it wouldn't be better to return pd.DataFrame(data=prior.rvs(), columns=prior.params)

        return np.array([[f.rvs() for f in self.functions] for _ in range(size)]).squeeze()


if __name__ == '__main__':

    import pandas as pd
    import matplotlib.pyplot as plt

    prior = MultiVariatePrior.by_range(
        MSP1_Merozoite_Kill_Fraction=SampleRange('linear', 0.4, 0.7),
        Nonspecific_Antigenicity_Factor=SampleRange('linear', 0.1, 0.9),
        Base_Gametocyte_Production_Rate=SampleRange('log', 0.001, 0.5))

    df = pd.DataFrame(data=prior.rvs(size=5000), columns=prior.params)

    n_bins = 50
    f, axs = plt.subplots(1, len(prior.params), figsize=(12, 4))
    for i, p in enumerate(prior.params):
        ax = axs[i]
        sample_range = prior.sample_functions[p].sample_range
        xscale = 'linear'
        if sample_range is None:
            stats = df[p].describe()
            vmin, vmax = stats.loc['min'], stats.loc['max']
            bins = np.linspace(stats.loc['min'], stats.loc['max'], n_bins)
        else:
            vmin, vmax = sample_range.range_min, sample_range.range_max
            if 'log' in sample_range.range_type:
                bins = np.logspace(np.log10(vmin), np.log10(vmax), n_bins)
                xscale = 'log'
            else:
                bins = np.linspace(vmin, vmax, n_bins)

        df[p].plot(kind='hist', ax=ax, bins=bins, alpha=0.5)
        ax.set(xscale=xscale, xlim=(vmin, vmax), title=p)

    f.set_tight_layout(True)

    plt.show()