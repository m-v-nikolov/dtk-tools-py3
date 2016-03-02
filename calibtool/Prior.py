import logging
from operator import mul

import numpy as np

logger = logging.getLogger(__name__)

'''
TODO:
- discrete distributions
- log-uniform, i.e. 10**uniform
- independent combinations of multi-variate normals
- Latin Hypercube Sampling?
'''


class MultiVariatePrior():
    '''
    Multi-variate wrapper exposing same interfaces
    as scipy.stats functions, i.e. pdf and rvs

    Different dimensions are drawn independently
    from the univariate distributions.

    : param functions : list of frozen scipy.stats function objects
    '''

    def __init__(self, functions, params=[], name=None):
        self.functions = functions
        self.params = params
        self.name = name

    @classmethod
    def by_param(cls, **param_priors):
        functions = param_priors.values()
        params = param_priors.keys()
        return cls(functions, params)

    def pdf(self, X):

        input_dim = X.ndim if X.ndim==1 else X.shape[1]

        if input_dim == 1:
            X = np.reshape(X, (X.shape[0], 1))

        if len(self.functions) == input_dim:
            logger.debug('Input dimension = %d', input_dim)
        else:
            raise Exception('Wrong shape')

        pdfs = []
        for params in X:
            pdfs.append(reduce(mul, [f.pdf(x) for f, x in zip(self.functions, params)], 1))  # product of individual function PDFs
        return np.array(pdfs)

    def rvs(self, size=1):
        return np.array([[f.rvs() for f in self.functions] for _ in range(size)]).squeeze()
