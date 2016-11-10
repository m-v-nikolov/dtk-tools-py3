import copy
import threading
from abc import abstractmethod, ABCMeta

from simtools.DataAccess.DataStore import DataStore


class BaseSimulationCreator(threading.Thread):
    __metaclass__ = ABCMeta

    def __init__(self, config_builder, experiment_builder,  function_set, setup, experiment, semaphore):
        super(BaseSimulationCreator, self).__init__()
        self.config_builder = config_builder
        self.experiment = experiment
        self.experiment_builder = experiment_builder
        self.function_set = function_set
        self.setup = setup
        self.semaphore = semaphore
        self.lib_staging_root = self.setup.get('lib_staging_root')
        self.asset_service = self.setup.get('use_comps_asset_svc',False)

    def run(self):
        try:
            self.process()
        except Exception as e:
            print "Exception during commission"
            print e
        finally:
            self.semaphore.release()

    def process(self):
        created_simulations = []
        for mod_fn_list in self.function_set:
            cb = copy.deepcopy(self.config_builder)

            # modify next simulation according to experiment builder
            # also retrieve the returned metadata
            tags = {}
            for func in mod_fn_list:
                md = func(cb)
                tags.update(md)

            # Stage the required dll for the experiment
            cb.stage_required_libraries(self.setup.get('dll_path'), self.lib_staging_root, self.asset_service)

            # Create the simulation
            s = self.create_simulation(cb)

            # Append the environment to the tag and add the default experiment tags if any
            if hasattr(self.experiment_builder, 'tags'):
                tags.update(self.experiment_builder.tags)
            self.set_tags_to_simulation(s, tags)

            # Add the files
            self.add_files_to_simulation(s, cb)

            # Add to the created simulations array
            created_simulations.append(s)

        self.post_creation()

        # Now that the save is done, we have the ids ready -> add the simulations to the experiment
        for sim in created_simulations:
            if not self.experiment.contains_simulation(sim.id):
                sim = DataStore.create_simulation(id=sim.id, tags=sim.tags)
                self.experiment.simulations.append(sim)

    @abstractmethod
    def create_simulation(self, cb):
        pass

    @abstractmethod
    def post_creation(self):
        pass

    @abstractmethod
    def add_files_to_simulation(self, s, cb):
        pass

    @abstractmethod
    def set_tags_to_simulation(self, s, tags):
        pass
