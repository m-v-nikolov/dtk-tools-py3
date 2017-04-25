import copy

from calibtool.algorithms.BaseNextPointAlgorithm import BaseNextPointAlgorithm


class GenericIterativeNextPoint(BaseNextPointAlgorithm):
    """
    Represents a Generic Next Point allowing thew Calibtool to function as a more generic iterative process.
    Here a dictionary needs to be passed as the state. 
    For example:
    ```
       initial_state = [{
        'Run_Number': rn
        } for rn in range(2)]
        
    ```
    
    Then the results of the analyzers are stored in the self.data associating iteration with results.
    Both the initial state and the results are stored there allowing to easily refer to it.
    ```
        self.data = [
                        {
                        'Run_Number': 1
                        'results':{
                            'what_comes_from_analyzers':{}
                        },
                        ...
                    ]
    ```      
    
    Note that the results needs to be contained in a Dictionary. 
    If you want to leverage pandas.DataFrame instead, you should use OptimTool. 
    """
    def __init__(self, initial_state):
        self.data = [
            {
                'iteration':0,
                'samples':initial_state
            }
        ]

    def restore(self, iteration_state):
        pass

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