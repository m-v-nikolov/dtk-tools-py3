from __future__ import print_function
import copy
from abc import abstractmethod, ABCMeta
from simtools import utils
from simtools.DataAccess.DataStore import DataStore
from multiprocessing import Process


class BaseSimulationCreator(Process):
    """
    Simulation creator base class.
    For compatibility issues, for now forces to be a Thread if ran on MacOS.
    """
    __metaclass__ = ABCMeta

    def __init__(self, config_builder, initial_tags,  function_set, max_sims_per_batch,experiment, setup, callback, return_list):
        super(BaseSimulationCreator, self).__init__()
        self.config_builder = config_builder
        self.experiment = experiment
        self.initial_tags = initial_tags
        self.function_set = function_set
        self.max_sims_per_batch = max_sims_per_batch
        self.return_list=return_list
        # Extract the path we want from the setup
        # Cannot use self.setup because the selected_block selection is lost during forking
        self.lib_staging_root = utils.translate_COMPS_path(setup.get('lib_staging_root'))
        self.asset_service = setup.getboolean('use_comps_asset_svc')
        self.dll_path = setup.get('dll_path')
        self.callback = callback
        self.created_simulations = []

    def run(self):
        try:
            self.process()
        except Exception as e:
            print("Exception during commission")
            import traceback
            traceback.print_exc()

    def process(self):
        self.pre_creation()

        while self.function_set:
            mod_fn_list = self.function_set.pop()
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
            self.created_simulations.append(s)

            if len(self.created_simulations) % self.max_sims_per_batch == 0 or not self.function_set:
                self.process_batch()

    def process_batch(self):
        self.save_batch()

        # Now that the save is done, we have the ids ready -> create the simulations
        while self.created_simulations:
            sim = self.created_simulations.pop()
            self.return_list.append(DataStore.create_simulation(id=str(sim.id), tags=sim.tags, experiment_id=self.experiment.exp_id))

        if self.callback: self.callback()

    @abstractmethod
    def create_simulation(self, cb):
        pass

    @abstractmethod
    def pre_creation(self):
        pass

    @abstractmethod
    def save_batch(self):
        pass

    @abstractmethod
    def add_files_to_simulation(self, s, cb):
        pass

    @abstractmethod
    def set_tags_to_simulation(self, s, tags):
        pass
