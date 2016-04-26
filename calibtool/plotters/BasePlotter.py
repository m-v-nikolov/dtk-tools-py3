from abc import ABCMeta, abstractmethod


class BasePlotter:
    __metaclass__ = ABCMeta

    def __init__(self, combine_sites=True):
        self.combine_sites = combine_sites
        self.all_results = None
        self.directory = None
        self.param_names = None
        self.site_analyzer_names = None

    @abstractmethod
    def visualize(self, calib_manager):
        pass