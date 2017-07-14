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

    def __init__(self, exp_list=[], analyzers=[], working_dir=None, force_analyze=False, verbose=True):
        self.experiments = []
        self.verbose = verbose
        self.analyzers = []
        with SetupParser.TemporarySetup() as sp:
            self.maxThreadSemaphore = multiprocessing.Semaphore(int(sp.get('max_threads', 16)))
        self.working_dir = working_dir or os.getcwd()
        self.parsers = []
        self.force_analyze = force_analyze

        # If no experiment is specified, retrieve the most recent as a convenience
        if exp_list == 'latest':
            exp_list = DataStore.get_most_recent_experiment()

        # Initial adding of experiments
        exp_list = exp_list if isinstance(exp_list, list) else [exp_list]
        map(self.add_experiment, exp_list)

        # Initial adding of the analyzers
        analyzers = analyzers if isinstance(analyzers, list) else [analyzers]
        map(self.add_analyzer, analyzers)

    def add_experiment(self, experiment):
        from simtools.DataAccess.Schema import Experiment
        if not isinstance(experiment, Experiment):
            experiment = retrieve_experiment(experiment)

        if experiment not in self.experiments:
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
            exp_manager.parserClass.createSimDirectoryMap(exp_id=exp_manager.experiment.exp_id,
                                                          suite_id=exp_manager.experiment.suite_id,
                                                          save=True, comps_experiment=exp_manager.comps_experiment,
                                                          verbose=self.verbose)
            if not exp_manager.asset_service:
                exp_manager.parserClass.asset_service = False

        p = ThreadPool()
        res = []
        for simulation in exp_manager.experiment.simulations:
            res.append(p.apply_async(self.parser_for_simulation, args=(simulation, experiment, exp_manager)))

        p.close()
        p.join()

        for r in res:
            parser = r.get()
            if parser: self.parsers.append(parser)

    def parser_for_simulation(self, simulation, experiment, manager):
        # If simulation not done -> return none
        if not self.force_analyze and simulation.status != SimulationState.Succeeded:
            if self.verbose: print "Simulation %s skipped (status is %s)" % (simulation.id, simulation.status.name)
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
            if self.verbose: print 'Simulation %s did not pass filter on any analyzer.' % simulation.id
            return

        # If all the analyzers present call for deactivating the parsing -> do it
        parse = any([a.parse for a in self.analyzers if hasattr(a,'parse')])

        # Create the parser
        return manager.get_output_parser(simulation, filtered_analyses, self.maxThreadSemaphore, parse)

    def analyze(self):
        # If no analyzers -> quit
        if len(self.analyzers) == 0:
            return

        # Create the parsers for the experiments
        map(self.create_parsers_for_experiment, self.experiments)

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
                if LocalOS.name == LocalOS.MAC:
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


