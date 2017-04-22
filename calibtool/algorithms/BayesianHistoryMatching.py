import logging
from sys import exit# as exit
import os
import pandas as pd 

import numpy as np
from scipy.stats import multivariate_normal
from scipy.spatial.distance import seuclidean
from scipy.stats import uniform, norm

import statsmodels.api as sm
import matplotlib.pyplot as plt

from calibtool.NextPointAlgorithm import NextPointAlgorithm

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


class BayesianHistoryMatching(NextPointAlgorithm):
    '''
    BayesianHistoryMatching

    The basic idea of BayesianHistoryMatching is
    '''

    def __init__(self, prior_fn,
                 n_initial_samples = 1e2,
                 n_samples_per_iteration = 1e2
             ):

        self.prior_fn = prior_fn
        self.n_initial_samples = int(n_initial_samples)
        self.n_samples_per_iteration = int(n_samples_per_iteration)

        initial_samples = self.sample_from_function(self.prior_fn, int(n_initial_samples))

        self.data = pd.DataFrame(initial_samples, columns=self.get_param_names())
        self.data['Iteration'] = 0
        self.data['Iteration'] = self.data['Iteration'].astype(int)
        self.data.index.name = '__sample_index__'
        self.data.reset_index(inplace=True)
        self.data['__sample_index__'] = self.data['__sample_index__'].astype(int)

        self.n_dimensions = self.data.shape[0]


    def add_samples(self, samples, iteration):
        samples_df = pd.DataFrame( samples, columns = self.get_param_names() )
        samples_df.index.name = '__sample_index__'
        samples_df['Iteration'] = iteration
        samples_df.reset_index(inplace=True)

        self.data = pd.concat([self.data, samples_df])

        logger.debug('__sample_index__:\n%s' % samples_df[self.get_param_names()].values)


    def choose_samples_for_next_iteration(self, iteration, results):
        logger.info('%s: Choosing samples at iteration %d:', self.__class__.__name__, iteration)
        logger.debug('Results:\n%s', results)

        data_by_iter = self.data.set_index('Iteration')
        if iteration+1 in data_by_iter.index.unique():
            # Perhaps the results have changed? Check?
            # TODO: Change to logger (everywhere)
            print "%s: I'm way ahead of you, samples for the next iteration were computed previously." % self.__class__.__name__
            return data_by_iter.loc[iteration+1, self.get_param_names()].values


        print 'WARNING, assuming working directory is Typhoid_History_Matching_NoDeaths'
        fn = os.path.join('Typhoid_History_Matching_NoDeaths', 'iter%d'%iteration, 'Candidates.xlsx')
        print 'Reading candidates from', fn

        candidates = pd.read_excel(fn, sheet_name='Values')

        print 'NOT SAVING SAMPLES !!!\n'*25
        #self.add_samples( candidates.as_matrix(), iteration+1 )

    def get_samples_for_iteration(self, iteration):
        return self.data.query('Iteration == @iteration').sort_values('__sample_index__')[self.get_param_names()]

    def end_condition(self):
        print "end_condition"
        # Stopping Criterion:
        # Return True to stop, False to continue
        logger.info('Continuing iterations ...')
        return False


    def get_final_samples(self):
        print "get_final_samples"
        '''
        Resample Stage:
        '''
        return dict(samples=self.data[self.get_param_names()].as_matrix())


    def prep_for_dict(self, df):
        # Needed for Windows compatibility
        #nulls = df.isnull()
        #if nulls.values.any():
        #    df[nulls] = None
        #return df.to_dict(orient='list')

        return df.where(~df.isnull(), other=None).to_dict(orient='list')


    def get_state(self):

        state = dict(
            n_dimensions = self.n_dimensions,
            #prior_fn = self.prior_fn,
            n_initial_samples = self.n_initial_samples,
            n_samples_per_iteration = self.n_samples_per_iteration,

            data = self.prep_for_dict(self.data),
            data_dtypes = {name:str(data.dtype) for name, data in self.data.iteritems()},
        )

        return state


    def set_state(self, state):
        self.n_dimensions = state['n_dimensions']
        #self.prior_fn = state['prior_fn']
        self.n_initial_samples = state['n_initial_samples']
        self.n_samples_per_iteration = state['n_samples_per_iteration']

        data_dtypes =state['data_dtypes']
        self.data = pd.DataFrame.from_dict(state['data'], orient='columns')
        for c in self.data.columns: # Argh
            self.data[c] = self.data[c].astype( data_dtypes[c] )

    def get_param_names(self):
        return self.prior_fn.params
