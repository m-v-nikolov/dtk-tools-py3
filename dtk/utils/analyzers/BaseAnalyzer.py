import logging
from abc import ABCMeta, abstractmethod

import pandas as pd

logger = logging.getLogger(__name__)


class BaseAnalyzer(object):
    """
    An abstract base class carrying the lowest level analyzer interfaces called by BaseExperimentManager
    """

    __metaclass__ = ABCMeta

    filenames = []

    @abstractmethod
    def __init__(self):
        self.data = None

    def filter(self, sim_metadata):
        """
        Decide whether analyzer should process a simulation based on its associated metadata
        :param sim_metadata: dictionary of tags associated with simulation
        :return: Boolean whether simulation should be analyzed by this analyzer
        """
        return True

    @abstractmethod
    def apply(self, parser):
        """
        In parallel for each simulation, consume raw data from filenames and emit selected data
        :param parser: simulation analysis worker thread object (i.e. OutputParser)
        :return: selected data for single simulation (to be joined in BaseAnalyzer.combine)
        """
        return pd.DataFrame()

    def combine(self, parsers):
        """
        On a single process, combine the selected data emitted for each simulation worker thread.
        :param parsers: simulation analysis worker thread objects (i.e. OutputParser)
        :return: combined data from all simulations
        """
        pass

    def finalize(self):
        """
        Make plots and collect any summary info.
        """
        # TODO: merge the "combine + finalize" interfaces; they're being called together in BaseExperimentManager?
        pass

    def plot(self):
        """
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
        # TODO: normalize the analyzer pattern with the calibtool BasePlotter and/or CalibAnalyzer plot_* staticmethods
        pass
