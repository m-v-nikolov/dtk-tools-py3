from abc import ABCMeta, abstractmethod


class ResampleManager(metaclass=ABCMeta):
    def __init__(self, calib_manager):
        self.calib_manager = calib_manager

    @abstractmethod
    def resample(self):
        pass

    def write_results(self, filename):
        pass


