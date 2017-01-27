from abc import ABCMeta, abstractmethod
from calibtool.utils import ResumePoint


class BasePlotter:
    __metaclass__ = ABCMeta

    def __init__(self, combine_sites=True, prior_fn={}):
        self.combine_sites = combine_sites
        self.prior_fn = prior_fn
        self.all_results = None
        self.directory = None
        self.param_names = None
        self.site_analyzer_names = None

    @abstractmethod
    def visualize(self, calib_manager):
        pass
