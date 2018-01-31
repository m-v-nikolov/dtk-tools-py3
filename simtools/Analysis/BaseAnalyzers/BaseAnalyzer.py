from abc import ABCMeta, abstractmethod


class BaseAnalyzer(metaclass=ABCMeta):
    """
    An abstract base class carrying the lowest level analyzer interfaces called by BaseExperimentManager
    """
    @abstractmethod
    def __init__(self, uid=None, working_dir=None, parse=True, need_dir_map=False, filenames=None):
        """
        :param uid: The unique id identifying this analyzer
        :param working_dir: A working directory to dump files
        :param parse: Do we want to leverage the OutputParser or just get the raw data in the select_simulation_data()
        :param need_dir_map: Will we need the path of the simulations eventually?
        :param filenames: Which files the analyzer needs to download
        """
        self.filenames = filenames or []
        self.parse = parse
        self.need_dir_map = need_dir_map
        self.working_dir = working_dir
        self.uid = uid or self.__class__.__name__
        self.results = None  # Store what finalize() is returning

    def initialize(self):
        """
        Called once after the analyzer has been added to the AnalyzeManager.
        Everything depending on the working directory or uid should be here instead of in __init__
        """
        pass

    def per_experiment(self, experiment):
        """
        Called once per experiment before doing the apply on the simulations
        :param experiment:
        """
        pass

    def filter(self, simulation):
        """
        Decide whether analyzer should process a simulation
        :param simulation: simulation object
        :return: Boolean whether simulation should be analyzed by this analyzer
        """
        return True

    def select_simulation_data(self, data, simulation):
        """
        In parallel for each simulation, consume raw data from filenames and emit selected data
        :param data: simulation data. Dictionary associating filename with content
        :param simulation: object representing the simulation for which the data is passed
        :return: selected data for the given simulation
        """
        return {}

    def finalize(self, all_data):
        """
        On a single process, get all the selected data
        :param all_data: dictionary associating simulation:selected_data
        """
        pass

