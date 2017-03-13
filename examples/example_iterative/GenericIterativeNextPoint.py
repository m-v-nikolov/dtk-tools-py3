import copy
import json

import pandas as pd

from calibtool.algo.BaseNextPointAlgorithm import BaseNextPointAlgorithm


class GenericIterativeNextPoint(BaseNextPointAlgorithm):
    def __init__(self, initial_state):
        self.data = [
            {
                'iteration':0,
                'samples':initial_state
            }
        ]

    def set_state(self, state, iteration):
        pass

    def cleanup(self):
        pass

    def get_param_names(self):
        return []

    def get_samples_for_iteration(self, iteration):
        return self.data[iteration]['samples']

    def get_state(self):
        return self.data

    def prep_for_dict(self, df):
        return df.where(~df.isnull(), other=None).to_dict(orient='list')

    def set_results_for_iteration(self, iteration, results):
        resultsdict = results.to_dict(orient='list').values()[0]
        new_iter = copy.deepcopy(self.data[iteration])
        new_iter['iteration'] = iteration+1
        for idx,sample in enumerate(new_iter['samples']): sample.update(resultsdict[idx])
        self.data.append(new_iter)

    def end_condition(self):
        return False

    def get_final_samples(self):
        return {}

    def update_summary_table(self, iteration_state, previous_results):
        return self.data, self.data #json.dumps(self.data, indent=3)

    def get_results_to_cache(self, results):
        return results.to_dict(orient='list')