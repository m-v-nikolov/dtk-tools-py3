from COMPS.Data import Simulation, Configuration
from COMPS.Data import SimulationFile
from simtools.SetupParser import SetupParser
from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator
from simtools.Utilities.COMPSUtilities import COMPS_login
from simtools.Utilities.General import nostdout


class COMPSSimulationCreator(BaseSimulationCreator):
    def __init__(self, config_builder, initial_tags,  function_set, max_sims_per_batch,experiment, callback, return_list, save_semaphore, asset_cache):
        super(COMPSSimulationCreator, self).__init__(config_builder, initial_tags,  function_set, max_sims_per_batch, experiment, callback, return_list, asset_cache)

        # Store the environment and endpoint
        self.environment = SetupParser.get('environment')
        self.server_endpoint = SetupParser.get('server_endpoint')
        self.save_semaphore = save_semaphore

    def create_simulation(self, cb):
        name = cb.get_param('Config_Name') if cb.get_param('Config_Name') else self.experiment.exp_name
        return Simulation(name=name, experiment_id=self.experiment.exp_id,
                          configuration=Configuration(asset_collection_id=cb.assets.collection_id))

    def save_batch(self):
        # Batch save after all sims in list have been added
        self.save_semaphore.acquire()
        try:
            with nostdout(stderr=True):
                Simulation.save_all(lambda *args: None)
        finally:
            self.save_semaphore.release()

    def add_files_to_simulation(self,s,cb):
        files = cb.dump_files_to_string()
        for name, content in files.iteritems():
            s.add_file(simulationfile=SimulationFile(name, 'input'), data=content)

    def set_tags_to_simulation(self, s, tags, cb):
        # Also add the environment
        tags['environment'] = self.environment

        # And the collections ids if exits
        if cb.assets:
            for collection_type, collection in cb.assets.collections.items():
                tags["%s_collection_id"%collection_type] = str(collection.collection_id)

        s.set_tags(tags)

    def pre_creation(self):
        # Call login now (even if we are already logged in, we need to call login to initialize the COMPSAccess Client)
        COMPS_login(self.server_endpoint)


