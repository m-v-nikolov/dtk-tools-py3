import collections
import itertools
import os
import sys
import time
from multiprocessing.pool import Pool

from COMPS.Data.Simulation import SimulationState

from simtools.Analysis.DataRetrievalProcess import retrieve_data
from simtools.DataAccess.DataStore import DataStore
from simtools.SetupParser import SetupParser
from simtools.Utilities import on_off, pluralize, verbose_timedelta
from simtools.Utilities.COMPSCache import COMPSCache
from simtools.Utilities.CacheEnabled import CacheEnabled
from simtools.Utilities.Experiments import retrieve_experiment, retrieve_simulation
from simtools.Utilities.General import init_logging, animation

logger = init_logging('AnalyzeManager')

ANALYZE_TIMEOUT = 3600  # Maximum seconds before timing out - set to 1h
WAIT_TIME = 1.15        # How much time to wait between check if the analysis is done
EXCEPTION_KEY = "__EXCEPTION__"


class AnalyzeManager(CacheEnabled):
    def __init__(self, exp_list=None, sim_list=None, analyzers=None, working_dir=None, force_analyze=False,
                 verbose=True):
        super().__init__()
        self.analyzers = []
        self.experiments = set()
        self.simulations = {}
        self.ignored_simulations = {}

        with SetupParser.TemporarySetup() as sp:
            self.max_threads = min(os.cpu_count(), int(sp.get('max_threads', 16)))
        self.verbose = verbose
        self.force_analyze = force_analyze
        self.working_dir = working_dir or os.getcwd()

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

        # Initialize the cache
        self.cache = self.initialize_cache(shards=self.max_threads)

    def filter_simulations(self, simulations):
        if self.force_analyze:
            self.simulations.update({s.id:s for s in simulations})
        else:
            for s in simulations:
                if s.status != SimulationState.Succeeded:
                    self.ignored_simulations[s.id] = s
                else:
                    self.simulations[s.id] = s

    def add_experiment(self, experiment):
        from simtools.DataAccess.Schema import Experiment
        from simtools.Utilities.COMPSUtilities import COMPS_login

        if not isinstance(experiment, Experiment):
            experiment = retrieve_experiment(experiment)

        if experiment not in self.experiments:
            self.experiments.add(experiment)
            if experiment.location == "HPC":
                COMPS_login(experiment.endpoint)
                COMPSCache.load_experiment(experiment.exp_id)

        self.filter_simulations(experiment.simulations)
        self.experiments.add(experiment)

    def add_simulation(self, simulation):
        from simtools.DataAccess.Schema import Simulation

        if not isinstance(simulation, Simulation):
            simulation = retrieve_simulation(simulation)

        self.filter_simulations([simulation])
        self.experiments.add(simulation.experiment)

    def add_analyzer(self, analyzer):
        # First check if we need to change the UID depending on other analyzers
        same_name = sum(1 if a.uid == analyzer.uid else 0 for a in self.analyzers)
        if same_name != 0:
            analyzer.uid += "_{}".format(same_name)

        # Then call the initialize method
        analyzer.working_dir = analyzer.working_dir or self.working_dir
        analyzer.initialize()

        self.analyzers.append(analyzer)

    def _check_exception(self):
        exception = self.cache.get(EXCEPTION_KEY, default=None)
        if exception:
            sys.stdout.flush()
            print("")
            print(exception)
            exit()

    def analyze(self):
        # Clear the cache
        self.cache.clear()

        # Start the timer
        start_time = time.time()

        # If no analyzers -> quit
        if not all((self.analyzers, self.simulations)):
            print("No analyzers or experiments selected, exiting...")
            return

        # If any of the analyzer needs the dir map, create it
        if any(a.need_dir_map for a in self.analyzers if hasattr(a, 'need_dir_map')):
            # preload the global dir map
            from simtools.Utilities.SimulationDirectoryMap import SimulationDirectoryMap
            for experiment in self.experiments:
                SimulationDirectoryMap.preload_experiment(experiment)

        # Run the per experiment on the analyzers
        for exp in self.experiments:
            for a in self.analyzers:
                a.per_experiment(exp)

        scount = len(self.simulations)
        max_threads = min(self.max_threads, scount if scount != 0 else 1)

        # Display some info
        if self.verbose:
            print("Analyze Manager")
            print(" | {} simulation{} - {} experiment{}"
                  .format(scount, pluralize(scount), len(self.experiments), pluralize(self.experiments)))
            print(" | force_analyze is {} and {} simulation{} ignored"
                  .format(on_off(self.force_analyze), len(self.ignored_simulations), pluralize(self.ignored_simulations)))
            print(" | Analyzer{}: ".format(pluralize(self.analyzers)))
            for a in self.analyzers:
                print(" |  - {} (Directory map: {} / File parsing: {} / Use cache: {})"
                      .format(a.uid, on_off(a.need_dir_map), on_off(a.parse), on_off(hasattr(a, "cache"))))
            print(" | Pool of {} analyzing processes".format(max_threads))

        pool = Pool(max_threads)
        if scount == 0 and self.verbose:
            print("No experiments/simulations for analysis.")
        else:
            results = pool.starmap_async(retrieve_data, itertools.product(self.simulations.values(), (self.analyzers,), (self.cache,)))

            while not results.ready():
                self._check_exception()

                time_elapsed = time.time()-start_time
                if self.verbose:
                    sys.stdout.write("\r {} Analyzing {}/{}... {} elapsed"
                                     .format(next(animation), len(self.cache), scount, verbose_timedelta(time_elapsed)))
                    sys.stdout.flush()

                if time_elapsed > ANALYZE_TIMEOUT:
                    raise Exception("Timeout while waiting the analysis to complete...")

                time.sleep(WAIT_TIME)
            results.get()

        # At this point we have all our results
        # Give to the analyzer
        finalize_results = {}
        for a in self.analyzers:
            analyzer_data = {}
            for key in self.cache:
                if key == EXCEPTION_KEY: continue
                # Retrieve the cache content and the simulation object
                sim_cache = self.cache.get(key)
                simulation_obj = self.simulations[key]
                # Give to the analyzer
                analyzer_data[simulation_obj] = sim_cache[a.uid] if sim_cache and a.uid in sim_cache else None
            finalize_results[a.uid] = pool.apply_async(a.finalize, (analyzer_data,))

        pool.close()
        pool.join()

        for a in self.analyzers:
            a.results = finalize_results[a.uid].get()

        if self.verbose:
            total_time = time.time() - start_time
            print("\r | Analysis done. Took {} (~ {:.3f} per simulation)"
                  .format(verbose_timedelta(total_time), total_time / scount if scount != 0 else 0))

