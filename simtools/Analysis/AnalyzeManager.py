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

from core.utils.time import verbose_timedelta
from simtools.Analysis.DataRetrievalProcess import retrieve_data
from simtools.DataAccess.DataStore import DataStore
from simtools.SetupParser import SetupParser
from simtools.Utilities.COMPSCache import COMPSCache
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation
from simtools.Utilities.General import init_logging, animation

logger = init_logging('AnalyzeManager')

ANALYZE_TIMEOUT = 3600  # Maximum seconds before timing out - set to 1h
WAIT_TIME = 1.15        # How much time to wait between check if the analysis is done


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
        # First check if we need to change the UID depending on other analyzers
        same_name = sum(1 if a.uid == analyzer.uid else 0 for a in self.analyzers)
        if same_name != 0:
            analyzer.uid += "_{}".format(same_name)

        # Then call the initialize method
        analyzer.working_dir = analyzer.working_dir or self.working_dir
        analyzer.initialize()

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

        simulations = dict()

        # Gather the simulations for the regular experiments
        for exp in self.experiments:
            for a in self.analyzers:
                a.per_experiment(exp)
            simulations.update({s.id:s for s in exp.simulations if self.force_analyze or s.status == SimulationState.Succeeded})

        # Gather the simulations for the standalones and count them along the way
        sa_count = 0
        for exp, sims in self.experiments_simulations.items():
            for a in self.analyzers:
                a.per_experiment(exp)
            sa_count += len(sims)
            simulations.update({s.id:s for s in sims if self.force_analyze or s.status == SimulationState.Succeeded})

        max_threads = min(self.max_threads, len(simulations))

        # Display some info
        if self.verbose:
            print("Analyze Manager")
            print(" | {} simulations (including {} stand-alones) from {} experiments"
                  .format(len(simulations), sa_count, len(self.experiments)))
            print(" | Analyzers: ")
            for a in self.analyzers:
                print(" |  - {} (Directory map: {} / File parsing: {} / Use cache: {})"
                      .format(a.uid, "on" if a.need_dir_map else "off", "on" if a.parse else "off", "yes" if hasattr(a, "cache") else "no"))
            print(" | Pool of {} analyzing processes".format(max_threads))

        # Create a temporary directory for the cache
        directory = mkdtemp()
        self.cache = FanoutCache(directory, shards=max_threads, timeout=1)

        if len(simulations) == 0 and self.verbose:
            print("No experiments/simulations for analysis.")
        else:
            pool = Pool(max_threads)
            results = pool.starmap_async(retrieve_data, itertools.product(simulations.values(), (self.analyzers,), (self.cache,)))
            pool.close()

            while not results.ready():
                time_elapsed = time.time()-start_time
                if self.verbose:
                    sys.stdout.write("\r {} Analyzing {}/{}... {:.2f}s elapsed"
                                     .format(next(animation), len(self.cache), len(simulations), verbose_timedelta(time_elapsed)))
                    sys.stdout.flush()

                if time_elapsed > ANALYZE_TIMEOUT:
                    raise Exception("Timeout while waiting the analysis to complete...")

                time.sleep(WAIT_TIME)

        # At this point we have all our results
        # Give to the analyzer
        for a in self.analyzers:
            analyzer_data = {}
            for key in self.cache:
                # Retrieve the cache content and the simulation object
                sim_cache = self.cache.get(key)
                simulation_obj = simulations[key]
                # Give to the analyzer
                analyzer_data[simulation_obj] = sim_cache[a.uid] if sim_cache and a.uid in sim_cache else None
            a.finalize(analyzer_data)

        # Close the cache and delete
        self.cache.close()
        shutil.rmtree(directory)

        if self.verbose:
            total_time = time.time() - start_time
            print("\r ✓ Analysis done. Took {:.1f}s (~ {:.3f}s per simulation)"
                  .format(verbose_timedelta(total_time), total_time/len(simulations)))

