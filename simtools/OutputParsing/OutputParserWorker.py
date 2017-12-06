import json
import os
from abc import ABCMeta, abstractmethod
from multiprocessing import Process, JoinableQueue, Queue, Manager
from multiprocessing.managers import BaseManager

from COMPS import Client
from COMPS.Data import Simulation, Experiment, QueryCriteria


def get_experiment_by_id(exp_id, query_criteria=None):
    return Experiment.get(exp_id, query_criteria=query_criteria)


def get_simulation_by_id(sim_id, query_criteria=None):
    return Simulation.get(id=sim_id, query_criteria=query_criteria)


def sims_from_experiment(e):
    return e.get_simulations(QueryCriteria().select(['id', 'state']).select_children('hpc_jobs'))


class BaseAnalyzer(object, metaclass=ABCMeta):
    """
    An abstract base class carrying the lowest level analyzer interfaces called by BaseExperimentManager
    """

    filenames = []  # Files for which raw data should be parsed for apply() function

    @abstractmethod
    def __init__(self):
        self.parse = True
        self.exp_id = None
        self.exp_name = None
        self.working_dir = None
        self.multiprocessing_plot = True

    def initialize(self):
        """
        Called once after the analyzer has been added to the AnalyzeManager
        """
        pass

    def per_experiment(self, experiment):
        """
        Called once per experiment before doing the apply on the simulations
        :param experiment:
        """
        pass

    def filter(self, sim_metadata):
        """
        Decide whether analyzer should process a simulation based on its associated metadata
        :param sim_metadata: dictionary of tags associated with simulation
        :return: Boolean whether simulation should be analyzed by this analyzer
        """
        return True

    def apply(self, parser):
        """
        In parallel for each simulation, consume raw data from filenames and emit selected data
        :param parser: simulation analysis worker thread object (i.e. OutputParser)
        :return: selected data for single simulation (to be joined in BaseAnalyzer.combine)
        """
        return None

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
        # TODO: normalize the analyzer pattern with the BaseComparisonAnalyzer.plot_comparison
        pass

def COMPS_login(endpoint):
    try:
        am = Client.auth_manager()
    except:
        Client.login(endpoint)

    return Client


class ParserData:
    def __init__(self, simulation):
        self.sim_id = simulation.id
        self._sim_path = None
        self.sim_data = simulation.tags
        # self.experiment = simulation.experiment
        self.simulation = simulation
        self.raw_data = {}
        self.selected_data = {}


class OutputParserWorker(Process):
    def __init__(self, simulation_queue, return_queue, filenames, analyzers):
        super(OutputParserWorker, self).__init__()
        self.simulation_queue = simulation_queue
        self.return_queue = return_queue
        self.filenames = filenames
        self.parse = True
        self.analyzers = analyzers

    def run(self):
        while True:
            # Get the next simulation in queue
            simulation = self.simulation_queue.get()

            # None was passed? We are at the end of the queue
            if simulation is None:
                self.simulation_queue.task_done()
                break

            # Process the simulation
            try:
                result = self.process_simulation(simulation)
                for i in range(len(self.analyzers)):
                    print(self.analyzers[i])
                    self.analyzers[i].apply(result)
                    # a.apply(result)

                del result.raw_data
                # Apply should appear here if possible to not send back the trimmed data
                self.return_queue.put(result)
            finally:
                # Inform the queue we are done
                self.simulation_queue.task_done()

    def process_simulation(self, simulation):
        # Create a ParserData
        pdata = ParserData(simulation)

        # Add it the raw data
        # if simulation.experiment.location == "HPC":
        if True:
            COMPS_login("https://comps.idmod.org")
            COMPS_simulation = get_simulation_by_id(simulation.id)
            asset_byte_arrays = COMPS_simulation.retrieve_output_files(paths=self.filenames)
            for filename, byte_array in zip(self.filenames, asset_byte_arrays):
                pdata.raw_data[filename] = self.load_single_file(filename, byte_array)
        else:
            for filepath in self.filenames:
                filename = os.path.basename(filepath)
                path = os.path.join(simulation.get_path(), filepath)
                content = open(path, 'rb').read()
                pdata.raw_data[filename] = self.load_single_file(filename, content)

        return pdata

    def load_single_file(self, filename, content=None):
        file_extension = os.path.splitext(filename)[1][1:].lower()
        if not self.parse:
            return content
        elif file_extension == 'json':
            return json.loads(content)
        else:
            return content

def process_simulation(simulation, filenames):
    # Create a ParserData
    pdata = ParserData(simulation)

    # Add it the raw data
    if simulation.experiment.location == "HPC":
        COMPS_login("https://comps.idmod.org")
        COMPS_simulation = get_simulation_by_id(simulation.id)
        asset_byte_arrays = COMPS_simulation.retrieve_output_files(paths=filenames)
        for filename, byte_array in zip(filenames, asset_byte_arrays):
            pdata.raw_data[filename] =byte_array
    else:
        for filepath in filenames:
            filename = os.path.basename(filepath)
            path = os.path.join(simulation.get_path(), filepath)
            content = open(path, 'rb').read()
            pdata.raw_data[filename] = content

    return pdata

def process_simulation_star(args):
    return process_simulation(*args)

class MyAnalyzer(BaseAnalyzer):
    filenames = ['config.json']
    def __init__(self):
        super(MyAnalyzer, self).__init__()
        self.simdur = {}

    def apply(self, parser):
        self.simdur[parser.sim_id] = parser.raw_data['config.json']['parameters']['Simulation_Duration']
        print(self.simdur)

    def finalize(self):
        print(self.simdur)


class AnalyzeManager:
    def __init__(self):
        self.experiments = []
        self.analyzers = []

    def analyze(self):
        # Get the unique filenames to retrieve
        filenames = set()
        manager = Manager()
        analyzers = manager.list()

        for a in self.analyzers:
            filenames.update(a.filenames)
            analyzers.append(a)

        simulations = JoinableQueue()
        results = Queue()
        num_processes = 8
        COMPS_login("https://comps.idmod.org")

        # Create the workers
        workers = [OutputParserWorker(simulations, results, filenames, analyzers) for _ in
                   range(num_processes)]

        # Start the workers
        for w in workers:
            w.start()

        # Add some sims
        exp = get_experiment_by_id('269e6b42-3593-e711-9401-f0921c16849d')
        sims = sims_from_experiment(exp)[:10]
        for s in sims:
            simulations.put(s)

        # Add poison
        for i in range(num_processes):
            simulations.put(None)

        processed = len(sims)
        parser_data = []
        while processed:
            result = results.get()
            # for a in self.analyzers:
            #     a.apply(result)
            # del result.raw_data

            parser_data.append(result)

            processed -= 1

        for w in workers:
            w.join()

        for analyzer in analyzers:
            analyzer.finalize()



if __name__ == "__main__":
    am = AnalyzeManager()
    am.analyzers.append(MyAnalyzer())
    am.analyze()





