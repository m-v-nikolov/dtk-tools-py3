from COMPS.Data import Simulation, Configuration
from COMPS.Data import SimulationFile
from simtools.SetupParser import SetupParser
from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator
from simtools.Utilities.COMPSUtilities import COMPS_login, get_experiment_by_id
from simtools.Utilities.General import nostdout


class COMPSSimulationCreator(BaseSimulationCreator):
    def __init__(self, config_builder, initial_tags,  function_set, max_sims_per_batch, experiment, cache, save_semaphore, comps_experiment):
        super(COMPSSimulationCreator, self).__init__(config_builder, initial_tags,  function_set, max_sims_per_batch, experiment, cache)

        # Store the environment and endpoint
        self.server_endpoint = SetupParser.get('server_endpoint')
        self.save_semaphore = save_semaphore
        self.comps_experiment = comps_experiment

    def create_simulation(self, cb):
        name = cb.get_param('Config_Name') or self.experiment.exp_name
        return Simulation(name=name, experiment_id=self.experiment.exp_id,
                          configuration=Configuration(asset_collection_id=cb.assets.collection_id))

    def save_batch(self):
        # Batch save after all sims in list have been added
        with nostdout(stderr=True):
            Simulation.save_all(save_semaphore=self.save_semaphore)

    def post_creation(self):
        # We may encounter 400 Bad Request if already commissioned but still we want to try commissioning every time
        try:
            self.comps_experiment.commission()
        except RuntimeError:
            pass

    def add_files_to_simulation(self, s, cb):
        files = cb.dump_files_to_string()
        for name, content in files.items():
            s.add_file(simulationfile=SimulationFile(name, 'input'), data=str.encode(content, 'utf-8'))

    def set_tags_to_simulation(self, s, tags, cb):
        # And the collections ids if exits
        if cb.assets:
            for collection_type, collection in cb.assets.collections.items():
                tags["%s_collection_id"%collection_type] = str(collection.collection_id)

        s.set_tags(tags)

    def pre_creation(self):
        # Call login now (even if we are already logged in, we need to call login to initialize the COMPSAccess Client)
        COMPS_login(self.server_endpoint)


