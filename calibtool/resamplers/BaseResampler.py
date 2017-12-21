from abc import ABCMeta, abstractmethod


class BaseResampler(metaclass=ABCMeta):
    def __init__(self, calib_manager):
        self.calib_manager = calib_manager

    @abstractmethod
    def resample(self):
        pass


