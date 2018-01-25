import collections
import itertools
import os
import shutil
import time
from multiprocessing.pool import Pool
from tempfile import mkdtemp

import sys
from COMPS.Data.Simulation import SimulationState
from diskcache import FanoutCache

from simtools.Analysis.DataRetrievalProcess import retrieve_data
from simtools.DataAccess.DataStore import DataStore
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSCache import COMPSCache
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation
from simtools.Utilities.General import init_logging, animation

logger = init_logging('AnalyzeManager')


class AnalyzeManager:
    def __init__(self, exp_list=None, sim_list=None, analyzers=None, working_dir=None, force_analyze=False, verbose=True):
        self.experiments = []
        self.simulations = []
        self.analyzers = []
        self.experiments_simulations = {}
        with SetupParser.TemporarySetup() as sp:
            self.max_threads = min(os.cpu_count(), int(sp.get('max_threads', 16)))
        self.verbose = verbose
        self.force_analyze = force_analyze
        self.working_dir = working_dir or os.getcwd()
        self.cache = None

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
            if experiment.location == "HPC":
                COMPSCache.load_experiment(experiment.exp_id)

    def add_simulation(self, simulation):
        from simtools.DataAccess.Schema import Simulation
        if not isinstance(simulation, Simulation):
            simulation = retrieve_simulation(simulation)

        experiment = simulation.experiment

        if experiment not in self.experiments_simulations:
            self.experiments_simulations[experiment] = [simulation]
        else:
            self.experiments_simulations[experiment].append(simulation)

        if experiment.location == "HPC":
            COMPSCache.load_simulation(simulation.id)

    def add_analyzer(self, analyzer):
        analyzer.working_dir = analyzer.working_dir or self.working_dir
        analyzer.initialize()

        same_type = sum(1 if type(a) == type(analyzer) else 0 for a in self.analyzers)
        if same_type != 0:
            analyzer.uid += "_{}".format(same_type)

        self.analyzers.append(analyzer)

    def analyze(self):
        start_time = time.time()
        # If no analyzers -> quit
        if len(self.analyzers) == 0:
            return

        # If any of the analyzer needs the dir map, create it
        if any(a.need_dir_map for a in self.analyzers if hasattr(a, 'need_dir_map')):
            # preload the global dir map
            from simtools.Utilities.SimulationDirectoryMap import SimulationDirectoryMap
            for experiment in self.experiments:
                SimulationDirectoryMap.preload_experiment(experiment)

        simulations = set()

        # Gather the simulations for the experiments
        for exp in self.experiments + list(self.experiments_simulations.keys()):
            for a in self.analyzers:
                a.per_experiment(exp)

            # Simulations to handle
            if exp in self.experiments_simulations:
                simulations.update(s for s in self.experiments_simulations[exp])
            else:
                simulations.update(exp.simulations)

        # Remove the simulation not finished (if not force analyze)
        if not self.force_analyze:
            simulations = [s for s in simulations if s.status == SimulationState.Succeeded]
        else:
            simulations = list(simulations)

        max_threads = min(self.max_threads, len(simulations))
        sa_count = sum(len(s) for s in self.experiments_simulations.values())

        # Display some info
        if self.verbose:
            print("Analyze Manager")
            print(" | {} simulations (including {} stand-alones) from {} experiments"
                  .format(len(simulations), sa_count, len(self.experiments)))
            print(" | Analyzers: ")
            for a in self.analyzers:
                print(" |  - {} (Directory map: {} / File parsing: {})"
                      .format(a.uid, "on" if a.need_dir_map else "off", "on" if a.parse else "off"))
            print(" | Pool of {} analyzing processes".format(max_threads))

        directory = mkdtemp()
        self.cache = FanoutCache(directory, shards=max_threads, timeout=1)
        if len(simulations) == 0 and self.verbose:
            print("No experiments/simulations for analysis.")
        else:

            pool = Pool(max_threads)
            r = pool.starmap_async(retrieve_data, itertools.product(simulations, (self.analyzers,), (self.cache,)))
            pool.close()

            while not r.ready():
                if self.verbose:
                    sys.stdout.write("\r {} Analyzing {}/{}... {:.2f}s elapsed"
                                     .format(next(animation), len(self.cache), len(simulations), time.time()-start_time))
                    sys.stdout.flush()
                    time.sleep(1.15)

        # At this point we have all our results
        # Give to the analyzer
        for a in self.analyzers:
            analyzer_data = {}
            for key in self.cache:
                analyzer_data[key] = self.cache.get(key)[a.uid]
            a.finalize(analyzer_data)

        self.cache.close()
        shutil.rmtree(directory)

        if self.verbose:
            total_time = time.time() - start_time
            print("\r | Analysis done. Took {:.1f}s (~ {:.3f}s per simulation)"
                  .format(total_time, total_time/len(simulations)))

