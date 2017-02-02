import logging
from abc import ABCMeta, abstractmethod

logger = logging.getLogger(__name__)

class BaseAnalyzer:
    """
    A class to represent a BaseAnalyzer

    Plotting using the interactive Matplotlib outside of the plot() functions HAVE TO use the following form:
        def plot():
            import matplotlib.pyplot as plt
            plt.plot(channel_data)
            plt.show()
        from multiprocessing import Process
        plotting_process = Process(target=plot)
        plotting_process.start()

        If a Process is not spawned, it may end up in an infinite loop breaking the tools.
    """
    __metaclass__ = ABCMeta

    required_reference_types = []
    filenames = []
    LL_fn = lambda ref, sim: 1

    def __init__(self, name=None, weight=None):
        self.name = name
        self.weight = weight
        self.site = None
        self.setup = {}
        self.exp_id = None
        self.exp_name = None
        self.working_dir = None
        self.done_showing = False
        self.parse = True

    def set_setup(self, setup):
        self.setup = setup

    def filter(self, sim_metadata):
        #return sim_metadata.get('__site__', False) == self.site.name
        return lambda x : True

    def apply(self, parser):
        return {}  # emit sim/reference comparison

    def combine(self, parsers):
        self.data = {}  # combine comparisons by sample-index groups

    def finalize(self):
        pass  # make plots and return summary info

    def plot(self):
        pass
