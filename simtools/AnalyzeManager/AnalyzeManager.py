
import os

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
import multiprocessing
from simtools.Utilities.General import get_os, init_logging, nostdout

logger = init_logging('AnalyzeManager')
current_dir = os.path.dirname(os.path.realpath(__file__))


class AnalyzeManager:

    def __init__(self, exp_list=[], analyzers=[], setup=None, working_dir=None):
        if not setup:
            setup = SetupParser()
        self.experiments = []
        self.analyzers = []
        self.maxThreadSemaphore = multiprocessing.Semaphore(int(setup.get('max_threads', 16)))
        self.working_dir = working_dir or os.getcwd()
        self.parsers = []

        # If no experiment is specified, retrieve the most recent as a convenience
        if not exp_list:
            exp_list = DataStore.get_most_recent_experiment()

        # Initial adding of experiments
        exp_list = exp_list if isinstance(exp_list, list) else [exp_list]
        for exp in exp_list: self.add_experiment(exp)

        # Initial adding of the analyzers
        analyzers = analyzers if isinstance(analyzers, list) else [analyzers]
        for analyzer in analyzers: self.add_analyzer(analyzer)

    def add_experiment(self, experiment):
        self.experiments.append(experiment)

    def add_analyzer(self, analyzer, working_dir=None):
        analyzer.working_dir = working_dir or self.working_dir
        analyzer.initialize()

        self.analyzers.append(analyzer)

    def create_parsers_for_experiment(self, experiment):
        # Create a manager for the current experiment
        exp_manager = ExperimentManagerFactory.from_experiment(experiment)

        if exp_manager.location == 'HPC':
            # Get the sim map no matter what
            exp_manager.parserClass.createSimDirectoryMap(exp_manager.experiment.exp_id, exp_manager.experiment.suite_id)

            # Enable asset service if needed
            if exp_manager.assets_service:
                exp_manager.parserClass.enableAssetService()

            # Enable compression if needed
            if exp_manager.compress_assets:
                exp_manager.parserClass.enableCompression()

        for simulation in exp_manager.experiment.simulations:
            parser = self.parser_for_simulation(simulation, experiment, exp_manager)
            if parser:
                self.parsers.append(parser)

    def parser_for_simulation(self, simulation, experiment, manager):
        # Add the simulation_id to the tags
        simulation.tags['sim_id'] = simulation.id

        filtered_analyses = []
        for a in self.analyzers:
            # set the analyzer info for the current sim
            a.exp_id = experiment.exp_id
            a.exp_name = experiment.exp_name

            if a.filter(simulation.tags):
                filtered_analyses.append(a)

        if not filtered_analyses:
            logger.debug('Simulation %s did not pass filter on any analyzer.' % simulation.id)
            return

        parser = manager.get_output_parser(simulation.get_path(), simulation.id, simulation.tags, filtered_analyses, self.maxThreadSemaphore)

        return parser

    def analyze(self):
        # If no analyzers -> quit
        if len(self.analyzers) == 0:
            return

        # Create the parsers for the experiments
        for exp in self.experiments:
            self.create_parsers_for_experiment(exp)

        for parser in self.parsers:
            self.maxThreadSemaphore.acquire()
            parser.start()

        # We are all done, finish analyzing
        for p in self.parsers:
            p.join()

        plotting_processes = []
        from multiprocessing import Process
        for a in self.analyzers:
            a.combine({parser.sim_id: parser for parser in self.parsers})
            a.finalize()
            # Plot in another process
            try:
                # If on mac just plot and continue
                if get_os() == 'mac':
                    a.plot()
                    continue
                plotting_process = Process(target=a.plot)
                plotting_process.start()
                plotting_processes.append(plotting_process)
            except Exception as e:
                print e
                logger.error("Error in the plotting process for analyzer %s" % a)
                logger.error("Experiments list %s" % self.experiments)
                logger.error(e)

        for p in plotting_processes:
            p.join()

        import matplotlib.pyplot as plt
        plt.show()
