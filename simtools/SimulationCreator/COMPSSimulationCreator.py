from COMPS.Data import Simulation
from COMPS.Data import SimulationFile
from simtools import utils
from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator


class COMPSSimulationCreator(BaseSimulationCreator):

    def __init__(self, config_builder, experiment_builder, function_set, setup, experiment, semaphore):
        super(COMPSSimulationCreator, self).__init__(config_builder, experiment_builder,  function_set, setup, experiment, semaphore)

        # If the assets service is in use, the path needs to come from COMPS
        if self.asset_service:
            self.lib_staging_root = utils.translate_COMPS_path(self.setup.get('lib_staging_root'), self.setup)

    def create_simulation(self, cb):
        name = cb.get_param('Config_Name') if cb.get_param('Config_Name') else self.experiment.exp_name
        return Simulation(name=name, experiment_id=self.experiment.exp_id)

    def post_creation(self):
        # Batch save after all sims in list have been added
        Simulation.save_all()

    def add_files_to_simulation(self,s,cb):
        files = cb.dump_files_to_string()
        for name, content in files.iteritems():
            s.add_file(simulationfile=SimulationFile(name, 'input'), data=content)

    def set_tags_to_simulation(self,s, tags):
        s.set_tags(tags)
        # Also add the environment
        tags['environment'] = self.setup.get('environment')

