from abc import ABCMeta, abstractmethod

import numpy as np
import pandas as pd


class NextPointAlgorithm(metaclass=ABCMeta):

    def __init__(self):
        self.iteration = 0

    @abstractmethod
    def set_state(self, state, iteration):
        pass

    def restore(self, iteration_state):
        pass

    @abstractmethod
    def cleanup(self):
        pass

    @abstractmethod
    def get_param_names(self):
        pass

    @abstractmethod
    def get_samples_for_iteration(self, iteration):
       pass

    @abstractmethod
    def get_state(self):
        pass

    @abstractmethod
    def set_results_for_iteration(self, iteration, results):
        pass

    @abstractmethod
    def end_condition(self):
        pass

    @abstractmethod
    def get_final_samples(self):
        pass

    def update_iteration(self, iteration):
        """
        Update the current iteration state of the algorithm.
        """
        self.iteration = iteration

    def prep_for_dict(self, df):
        """
        Utility function allowing to transform a DataFrame into a dict removing null values
        """
        return df.where(~df.isnull(), other=None).to_dict(orient='list')

    @staticmethod
    def sample_from_function(function, N):
        return np.array([function.rvs() for i in range(N)])

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

