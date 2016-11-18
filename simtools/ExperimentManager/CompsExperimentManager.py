import os
import re
from datetime import datetime

from COMPS.Data import Configuration
from COMPS.Data import Experiment
from COMPS.Data import Priority
from COMPS.Data import Suite
from simtools import utils
from simtools.DataAccess.Schema import Simulation
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.OutputParser import CompsDTKOutputParser
from simtools.SimulationCreator.COMPSSimulationCreator import COMPSSimulationCreator


class CompsExperimentManager(BaseExperimentManager):
    """
    Extends the LocalExperimentManager to manage DTK simulations through COMPS wrappers
    e.g. creation of Simulation, Experiment, Suite objects
    """
    location = 'HPC'
    parserClass = CompsDTKOutputParser
    creatorClass = COMPSSimulationCreator

    def __init__(self, experiment, exp_data, setup=None):
        BaseExperimentManager.__init__(self, experiment, exp_data, setup)
        self.comps_sims_to_batch = int(self.get_property('sims_per_thread'))
        self.sims_to_create = []
        self.commissioners = []
        self.assets_service = self.setup.getboolean('use_comps_asset_svc')
        self.endpoint = self.setup.get('server_endpoint')
        self.compress_assets = self.setup.getboolean('compress_assets')
        utils.COMPS_login(self.endpoint)

    def check_input_files(self, input_files):
        """
        Check file exist and return the missing files as dict
        """
        input_root = self.setup.get('input_root')
        input_root_real = utils.translate_COMPS_path(input_root)
        return input_root_real, self.find_missing_files(input_files, input_root_real)

    def analyze_experiment(self):
        if not self.assets_service:
            self.parserClass.createSimDirectoryMap(self.experiment.exp_id, self.experiment.suite_id)
        if self.compress_assets:
            from simtools.utils import nostdout
            with nostdout():
                self.parserClass.enableCompression()

        super(CompsExperimentManager, self).analyze_experiment()

    def create_suite(self, suite_name):
        suite = Suite(suite_name)
        suite.save()

        return str(suite.id)

    def create_experiment(self, experiment_name,experiment_id=None, suite_id=None):
        # Also create the experiment in COMPS to get the ID
        utils.COMPS_login(self.setup.get('server_endpoint'))

        config = Configuration(
            environment_name=self.setup.get('environment'),
            simulation_input_args=self.commandline.Options,
            working_directory_root=os.path.join(self.setup.get('sim_root'), experiment_name + '_' + re.sub('[ :.-]', '_', str(datetime.now()))),
            executable_path=self.staged_bin_path,
            node_group_name=self.setup.get('node_group'),
            maximum_number_of_retries=int(self.setup.get('num_retries')),
            priority=Priority[self.setup.get('priority')],
            min_cores=self.config_builder.get_param('Num_Cores', 1),
            max_cores=self.config_builder.get_param('Num_Cores', 1),
            exclusive=self.config_builder.get_param('Exclusive', False)
        )

        e = Experiment(name=experiment_name,
                       configuration=config,
                       suite_id=suite_id)
        e.save()

        # Create experiment in the base class
        super(CompsExperimentManager, self).create_experiment(experiment_name,  str(e.id), suite_id)

        # Set some extra stuff
        self.experiment.endpoint = self.endpoint

    def create_simulation(self):
        files = self.config_builder.dump_files_to_string()

        # Create the tags and append the environment to the tag
        tags = self.exp_builder.metadata
        tags['environment'] = self.setup.get('environment')
        tags.update(self.exp_builder.tags if hasattr(self.exp_builder, 'tags') else {})

        # Add the simulation to the batch
        self.sims_to_create.append({'name': self.config_builder.get_param('Config_Name'), 'files':files, 'tags':tags})

    def commission_simulations(self, states):
        import threading
        from simtools.SimulationRunner.COMPSRunner import COMPSSimulationRunner
        t1 = threading.Thread(target=COMPSSimulationRunner, args=(self.experiment, states,self.success_callback, not self.done_commissioning()))
        t1.daemon = True
        t1.start()
        self.runner_created = True

    def cancel_experiment(self):
        super(CompsExperimentManager, self).cancel_experiment()
        utils.COMPS_login(self.endpoint)
        e = Experiment.get(self.experiment.exp_id)
        if e:
            e.cancel()

    def hard_delete(self):
        """
        Delete local cache data for experiment and marks the server entity for deletion.
        """
        # Perform soft delete cleanup.
        self.soft_delete()

        # Mark experiment for deletion in COMPS.
        utils.COMPS_login(self.endpoint)
        e = Experiment.get(self.experiment.exp_id)
        e.delete()

    def kill_simulation(self, simulation):
        utils.COMPS_login(self.endpoint)
        s = Simulation.get(simulation.id)
        s.cancel()
