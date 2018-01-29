from abc import ABCMeta, abstractmethod

class BaseSimulationRunner:
    __metaclass__ = ABCMeta

    MONITOR_SLEEP = 5 # seconds

    def __init__(self, experiment):
        self.experiment = experiment

    @abstractmethod
    def run(self):
        pass

    @abstractmethod
    def monitor(self):
        pass
