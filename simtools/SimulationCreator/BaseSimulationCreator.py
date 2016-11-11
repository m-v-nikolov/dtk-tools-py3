from __future__ import print_function
import copy
from abc import abstractmethod, ABCMeta
from multiprocessing import Process

from simtools import utils
from simtools.DataAccess.DataStore import DataStore


class BaseSimulationCreator(Process):
    __metaclass__ = ABCMeta

    def __init__(self, config_builder, initial_tags,  function_set, experiment, semaphore, sim_queue, setup, callback):
        super(BaseSimulationCreator, self).__init__()
        self.config_builder = config_builder
        self.experiment = experiment
        self.initial_tags = initial_tags
        self.function_set = function_set
        self.sim_queue = sim_queue
        self.semaphore = semaphore
        # Extract the path we want from the setup
        # Cannot use self.setup because the selected_block selection is lost during forking
        self.lib_staging_root = utils.translate_COMPS_path(setup.get('lib_staging_root'))
        self.asset_service = setup.get('use_comps_asset_svc',False)
        self.dll_path = setup.get('dll_path')
        self.callback = callback

    def run(self):
        try:
            self.process()
        except Exception as e:
            print("Exception during commission")
            import traceback
            traceback.print_exc()
        finally:
            self.semaphore.release()

    def process(self):
        self.pre_creation()
        created_simulations = []
        for mod_fn_list in self.function_set:
            cb = copy.deepcopy(self.config_builder)

            # modify next simulation according to experiment builder
            # also retrieve the returned metadata
            tags = self.initial_tags if self.initial_tags else {}
            for func in mod_fn_list:
                md = func(cb)
                tags.update(md)

            # Stage the required dll for the experiment
            cb.stage_required_libraries(self.dll_path,self.lib_staging_root, self.asset_service)

            # Create the simulation
            s = self.create_simulation(cb)

            # Append the environment to the tag and add the default experiment tags if any
            self.set_tags_to_simulation(s, tags)

            # Add the files
            self.add_files_to_simulation(s, cb)

            # Add to the created simulations array
            created_simulations.append(s)

        self.post_creation()

        # Now that the save is done, we have the ids ready -> add the simulations to the experiment
        for sim in created_simulations:
            if not self.experiment.contains_simulation(sim.id):
                self.sim_queue.put(DataStore.create_simulation(id=sim.id, tags=sim.tags, experiment_id=self.experiment.exp_id))

        if self.callback: self.callback()

    @abstractmethod
    def create_simulation(self, cb):
        pass

    @abstractmethod
    def pre_creation(self):
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
