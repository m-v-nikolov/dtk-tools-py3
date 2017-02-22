class GenericIterativeNextPoint:

    def choose_initial_samples(self):
        pass

    def set_initial_samples(self):
        pass

    def choose_next_point_samples(self, iteration):
        pass

    def get_samples_for_iteration(self, iteration):
        pass

    def add_samples(self, samples, iteration):
        pass

    def get_next_samples_for_iteration(self, iteration):
        pass

    def update_results(self, results):
        pass

    def update_state(self, iteration):
        pass

    def update_iteration(self, iteration):
        pass

    def end_condition(self):
        pass

    def get_next_samples(self):
        pass

    def get_final_samples(self):
        pass

    def get_state(self):
        pass

    def prep_for_dict(self, df):
        pass

    def set_state(self, state, iteration):
        pass

    def generate_variables_from_data(self):
        pass

    def next_point_fn(self):
        pass

    def verify_valid_samples(self, next_samples):
        pass

    def get_param_names(self):
        pass

    @staticmethod
    def sample_from_function(function, N):
        pass

    def cleanup(self):
        pass

    def restore(self, iteration_state):
        pass