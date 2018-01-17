import multiprocessing
import os
from multiprocessing.pool import ThreadPool

import collections
from COMPS.Data.Simulation import SimulationState

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.General import init_logging
from simtools.Utilities.LocalOS import LocalOS

from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation

logger = init_logging('AnalyzeManager')


class AnalyzeManager:
    def __init__(self, exp_list=None, sim_list=None, analyzers=None, working_dir=None, force_analyze=False, verbose=True,
                 create_dir_map=False):
        self.experiments = []
        self.simulations = []
        self.parsers = []
        self.analyzers = []
        self.experiments_simulations = {}

        self.verbose = verbose
        self.force_analyze = force_analyze
        self.create_dir_map = create_dir_map
        self.parse = True

        self.working_dir = working_dir or os.getcwd()

        with SetupParser.TemporarySetup() as sp:
            self.maxThreadSemaphore = multiprocessing.Semaphore(int(sp.get('max_threads', 16)))

        # If no experiment is specified, retrieve the most recent as a convenience
        if exp_list == 'latest':
            exp_list = DataStore.get_most_recent_experiment()

        # Initial adding of experiments
        if exp_list:
            exp_list = exp_list if isinstance(exp_list, collections.Iterable) and not isinstance(exp_list, str) else [exp_list]
            for exp in exp_list: self.add_experiment(exp)

        # Initial adding of the simulations
        if sim_list:
            sim_list = sim_list if isinstance(sim_list, collections.Iterable) else [sim_list]
            for sim in sim_list: self.add_simulation(sim)

        # Initial adding of the analyzers
        if analyzers:
            analyzer_list = analyzers if isinstance(analyzers, collections.Iterable) else [analyzers]
            for a in analyzer_list: self.add_analyzer(a)

    def add_experiment(self, experiment):
        from simtools.DataAccess.Schema import Experiment
        if not isinstance(experiment, Experiment):
            experiment = retrieve_experiment(experiment)

        if experiment not in self.experiments:
            self.experiments.append(experiment)

    def add_simulation(self, simulation):
        from simtools.DataAccess.Schema import Simulation
        if not isinstance(simulation, Simulation):
            simulation = retrieve_simulation(simulation)

        experiment = simulation.experiment

        if experiment.exp_id not in self.experiments_simulations:
            self.experiments_simulations[experiment.exp_id] = [simulation]
        else:
            self.experiments_simulations[experiment.exp_id].append(simulation)

    def add_analyzer(self, analyzer, working_dir=None):
        analyzer.working_dir = working_dir or self.working_dir
        analyzer.initialize()

        self.analyzers.append(analyzer)

    def create_parsers_for_experiment(self, experiment):
        # Create a manager for the current experiment
        exp_manager = ExperimentManagerFactory.from_experiment(experiment)

        # Refresh the experiment just to be sure to have latest info
        exp_manager.refresh_experiment()

        if exp_manager.location == 'HPC':
            # Get the sim map no matter what
            if self.create_dir_map:

                exp_manager.parserClass.createSimDirectoryMap(exp_id=exp_manager.experiment.exp_id,
                                                              suite_id=exp_manager.experiment.suite_id,
                                                              save=True, comps_experiment=exp_manager.comps_experiment,
                                                              verbose=self.verbose)
            if not exp_manager.asset_service:
                exp_manager.parserClass.asset_service = False

        # Call the analyzer per experiment function for initialization
        for analyzer in self.analyzers:
            analyzer.per_experiment(experiment)

        # Create the thread pool to create the parsers
        p = ThreadPool()

        # Simulations to handle
        if experiment.exp_id in self.experiments_simulations:
            simulations = self.experiments_simulations[experiment.exp_id]
            # drop experiment from self.experiments_simulations
            self.experiments_simulations.pop(experiment.exp_id)
        else:
            simulations = exp_manager.experiment.simulations

        results = [p.apply_async(self.parser_for_simulation, args=(s, experiment, exp_manager)) for s in simulations]

        p.close()
        p.join()

        # Retrieve the parsers from the pool (remove the None)
        self.parsers.extend(list(filter(None.__ne__, (r.get() for r in results))))

    def create_parsers_for_experiment_from_simulation(self, exp_id):
        experiment = retrieve_experiment(exp_id)
        self.create_parsers_for_experiment(experiment)

    def parser_for_simulation(self, simulation, experiment, manager):
        # If simulation not done -> return none
        if simulation.status != SimulationState.Succeeded and not self.force_analyze:
            if self.verbose: print("Simulation {} skipped (status is {})".format(simulation.id, simulation.status.name))
            return

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
            if self.verbose: print("Simulation {} did not pass filter on any analyzer.".format(simulation.id))
            return

        # Create the parser
        return manager.get_output_parser(simulation, filtered_analyses, self.maxThreadSemaphore, self.parse)

    def analyze(self):
        # If no analyzers -> quit
        if len(self.analyzers) == 0:
            return

        # Empty the parsers
        self.parsers = []

        # If all the analyzers present call for deactivating the parsing -> do it
        self.parse = any([a.parse for a in self.analyzers if hasattr(a, 'parse')])

        # Create the parsers for the experiments
        for exp in self.experiments:
            self.create_parsers_for_experiment(exp)

        # Create the parsers for the experiments of the standalone simulations
        for exp in list(self.experiments_simulations.keys()):
            self.create_parsers_for_experiment_from_simulation(exp)

        if len(self.parsers) == 0 and self.verbose:
            print("No experiments/simulations for analysis.")

        for parser in self.parsers:
            self.maxThreadSemaphore.acquire()
            parser.start()

        # We are all done, finish analyzing
        for parser in self.parsers:
            parser.join()

        plotting_processes = []
        from multiprocessing import Process
        for a in self.analyzers:
            a.combine({parser.sim_id: parser for parser in self.parsers})
            a.finalize()
            # Plot in another process
            try:
                # If on mac just plot and continue
                if LocalOS.name == LocalOS.MAC or (hasattr(a, 'multiprocessing_plot') and not a.multiprocessing_plot):
                    a.plot()
                    continue
                plotting_process = Process(target=a.plot)
                plotting_process.start()
                plotting_processes.append(plotting_process)
            except Exception as e:
                print(e)
                logger.error("Error in the plotting process for analyzer {}".format(a))
                logger.error("Experiments list {}".format(self.experiments))
                logger.error(e)

        for p in plotting_processes:
            p.join()

