import multiprocessing
import os
from multiprocessing.pool import ThreadPool

from COMPS.Data.Simulation import SimulationState

from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.ExperimentManagerFactory import ExperimentManagerFactory
from simtools.SetupParser import SetupParser
from simtools.Utilities.Experiments import retrieve_experiment
from simtools.Utilities.General import init_logging
from simtools.Utilities.LocalOS import LocalOS

logger = init_logging('AnalyzeManager')


current_dir = os.path.dirname(os.path.realpath(__file__))


class AnalyzeManager:
    def __init__(self, exp_list=[], sim_list=[], analyzer_list=[], working_dir=None, force_analyze=False, verbose=True,
                 create_dir_map=True):
        self.experiments = []
        self.simulations = []
        self.experiments_simulations = {}
        self.verbose = verbose
        self.analyzers = []
        with SetupParser.TemporarySetup() as sp:
            self.maxThreadSemaphore = multiprocessing.Semaphore(int(sp.get('max_threads', 16)))
        self.working_dir = working_dir or os.getcwd()
        self.parsers = []
        self.force_analyze = force_analyze
        self.create_dir_map = create_dir_map

        # If no experiment is specified, retrieve the most recent as a convenience
        if exp_list == 'latest':
            exp_list = DataStore.get_most_recent_experiment()

        # Initial adding of experiments
        exp_list = exp_list if isinstance(exp_list, list) else [exp_list]
        map(self.add_experiment, exp_list)

        # Initial adding of the analyzers
        sim_list = sim_list if isinstance(sim_list, list) else [sim_list]
        map(self.add_simulation, sim_list)

        # Initial adding of the analyzers
        analyzer_list = analyzer_list if isinstance(analyzer_list, list) else [analyzer_list]
        map(self.add_analyzer, analyzer_list)

    def add_experiment(self, experiment):
        from simtools.DataAccess.Schema import Experiment
        if not isinstance(experiment, Experiment):
            experiment = retrieve_experiment(experiment)

        if experiment not in self.experiments:
            self.experiments.append(experiment)

    def add_simulation(self, simulation):
        from simtools.DataAccess.Schema import Simulation
        if not isinstance(simulation, Simulation):
            simulation = DataStore.get_simulation(simulation)

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
        self.experiments_with_data = [] # This is to aid in gracefully handling failures due to no data

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
        res = []

        if experiment.exp_id in self.experiments_simulations:
            # only consider simulations provided
            for simulation in self.experiments_simulations[experiment.exp_id]:
                res.append(p.apply_async(self.parser_for_simulation, args=(simulation, experiment, exp_manager)))

            # drop experiment from self.experiments_simulations
            self.experiments_simulations.pop(experiment.exp_id)
        else:
            for simulation in exp_manager.experiment.simulations:
                res.append(p.apply_async(self.parser_for_simulation, args=(simulation, experiment, exp_manager)))

        p.close()
        p.join()

        # Retrieve the parsers from the pool
        data = False
        for r in res:
            parser = r.get()
            if parser:
                self.parsers.append(parser)
                data = True
        if data:
            self.experiments_with_data.append(experiment)

    def create_parsers_for_experiment_from_simulation(self, exp_id):
        experiment = retrieve_experiment(exp_id)
        self.create_parsers_for_experiment(experiment)

    def create_parser_for_simulation(self, simulation):
        experiment = simulation.experiment

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

        # Create a parser for given simulation
        parser = self.parser_for_simulation(simulation, experiment, exp_manager)
        self.parsers.append(parser)

    def parser_for_simulation(self, simulation, experiment, manager):
        # If simulation not done -> return none
        if not self.force_analyze and simulation.status != SimulationState.Succeeded:
            if self.verbose: print("Simulation %s skipped (status is %s)" % (simulation.id, simulation.status.name))
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
            if self.verbose: print("Simulation %s did not pass filter on any analyzer." % simulation.id)
            return

        # If all the analyzers present call for deactivating the parsing -> do it
        parse = any([a.parse for a in self.analyzers if hasattr(a,'parse')])

        # Create the parser
        return manager.get_output_parser(simulation, filtered_analyses, self.maxThreadSemaphore, parse)

    def analyze(self):
        # If no analyzers -> quit
        if len(self.analyzers) == 0:
            return

        # Empty the parsers
        self.parsers = []

        # Create the parsers for the experiments
        map(self.create_parsers_for_experiment, self.experiments)

        # Create the parsers for the experiments
        map(self.create_parsers_for_experiment_from_simulation, self.experiments_simulations.keys())

        # only process experiments that have at least some data in them
        # for experiment in self.experiments:
        #     if experiment not in self.experiments_with_data: # this is set in self.create_parsers_for_experiment
        #         print('Experiment %s has no simulations ready for analysis, skipping...' % experiment.exp_id)
        #         self.experiments.remove(experiment)

        if len(self.parsers) == 0:
            print('No experiments/simulations for analysis.')
            return # mimic the above len(self.analyzers) == 0 behavior

        for parser in self.parsers:
            self.maxThreadSemaphore.acquire()
            parser.start()

        # We are all done, finish analyzing
        map(lambda p: p.join(), self.parsers)

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
                print e
                logger.error("Error in the plotting process for analyzer %s" % a)
                logger.error("Experiments list %s" % self.experiments)
                logger.error(e)

        map(lambda p: p.join(), plotting_processes)


