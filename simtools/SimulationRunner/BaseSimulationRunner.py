from abc import ABCMeta, abstractmethod


class BaseSimulationRunner:
    __metaclass__ = ABCMeta

    def __init__(self, experiment, states, success, lock):
        self.experiment = experiment
        self.states = states
        self.success = success
        self.lock = lock

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def monitor(self):
        pass
