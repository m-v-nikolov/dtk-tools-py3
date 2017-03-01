import pandas as pd
import numpy as np

from calibtool.algo.BaseNextPointAlgorithm import BaseNextPointAlgorithm


class GenericIterativeNextPoint(BaseNextPointAlgorithm):
    def __init__(self,initial_values):
        self.initial_values = initial_values
        self.data = pd.DataFrame({
            'Iteration': 0,
            'Result': []
        })
        self.data['Result'] = self.data['Result'].astype(object)


    def set_state(self, state, iteration):
        self.data = pd.DataFrame.from_dict(state['data'], orient='columns')

    def cleanup(self):
        pass

    def get_param_names(self):
        return self.initial_values.keys()

    def get_samples_for_iteration(self, iteration):

        iterationData = pd.DataFrame({
            'Iteration': iteration,
            'Result': []
        })
        for param, values in self.initial_values.iteritems():
            param_df = pd.DataFrame({param: values, 'Iteration': iteration})
            iterationData = pd.merge(iterationData, param_df, on="Iteration", how='right')

        self.data = pd.concat([self.data,iterationData])

        return self.data[self.data['Iteration'] == iteration][self.get_param_names()]


    def get_state(self):
        return dict(data=self.prep_for_dict(self.data),
                    data_dtypes={name: str(data.dtype) for name, data in self.data.iteritems()})

    def prep_for_dict(self, df):
        return df.where(~df.isnull(), other=None).to_dict(orient='list')

    def set_results_for_iteration(self, iteration, results):
        self.data.loc[self.data['Iteration'] == iteration,"Result"] = results

    def end_condition(self):
        return False

    def get_final_samples(self):
        return {}