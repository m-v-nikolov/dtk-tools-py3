from abc import ABCMeta, abstractmethod


class BaseNextPointAlgorithm:
    __metaclass__ = ABCMeta

    @abstractmethod
    def set_state(self, state, iteration):
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
