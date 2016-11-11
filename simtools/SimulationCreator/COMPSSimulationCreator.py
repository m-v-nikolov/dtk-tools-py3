from COMPS.Data import Simulation
from COMPS.Data import SimulationFile
from simtools import utils
from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator
from simtools.utils import nostdout


class COMPSSimulationCreator(BaseSimulationCreator):
    def __init__(self, config_builder, initial_tags,  function_set, experiment, semaphore, sim_queue, setup, callback=None):
        super(COMPSSimulationCreator, self).__init__(config_builder, initial_tags,  function_set, experiment, semaphore, sim_queue, setup, callback)

        # Store the environment and endpoint
        self.environment = setup.get('environment')
        self.server_endpoint = setup.get('server_endpoint')

    def create_simulation(self, cb):
        name = cb.get_param('Config_Name') if cb.get_param('Config_Name') else self.experiment.exp_name
        return Simulation(name=name, experiment_id=self.experiment.exp_id)

    def post_creation(self):
        # Batch save after all sims in list have been added
        with nostdout():
            Simulation.save_all()

    def add_files_to_simulation(self,s,cb):
        files = cb.dump_files_to_string()
        for name, content in files.iteritems():
            s.add_file(simulationfile=SimulationFile(name, 'input'), data=content)

    def set_tags_to_simulation(self,s, tags):
        # Also add the environment
        tags['environment'] = self.environment
        s.set_tags(tags)

    def pre_creation(self):
        # Call login now (even if we are already logged in, we need to call login to initialize the COMPS Client)
        utils.COMPS_login(self.server_endpoint)


