import pandas as pd


class GenericIterativeNextPoint:
    def __init__(self,initial_values):
        self.initial_values = initial_values
        self.data = pd.DataFrame({
            'Iteration': 0,
            'Result': []
        })




    def get_param_names(self):
        return self.initial_values.keys()

    def get_samples_for_iteration(self, iteration):
        if iteration == 0:
            for param, values in self.initial_values.iteritems():
                param_df = pd.DataFrame({param: values, 'Iteration': 0})
                self.data = pd.merge(self.data, param_df, on="Iteration", how='right')
        else:
            for param, values in self.initial_values.iteritems():
                param_df = pd.DataFrame({param: values, 'Iteration': 1})
                self.data = pd.merge(self.data, param_df, on="Iteration", how='right')


        return self.data[self.data['Iteration'] == iteration][self.get_param_names()]


    def get_state(self):
        return dict(data=self.prep_for_dict(self.data),
                    data_dtypes={name: str(data.dtype) for name, data in self.data.iteritems()})

    def prep_for_dict(self, df):
        return df.where(~df.isnull(), other=None).to_dict(orient='list')

    def set_results_for_iteration(self, iteration, results):
        data_by_iter = self.data.set_index('Iteration')
        # Store results ... even if changed
        data_by_iter.loc[iteration, 'Result'] = results
        self.data = data_by_iter.reset_index()

    def end_condition(self):
        return False