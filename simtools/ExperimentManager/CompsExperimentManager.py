from simtools.Commisioner import CompsSimulationCommissioner
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.OutputParser import CompsDTKOutputParser
from simtools import utils


class CompsExperimentManager(BaseExperimentManager):
    """
    Extends the LocalExperimentManager to manage DTK simulations through COMPS wrappers
    e.g. creation of Simulation, Experiment, Suite objects
    """
    location = 'HPC'
    parserClass = CompsDTKOutputParser

    def __init__(self, experiment, exp_data, setup=None):
        BaseExperimentManager.__init__(self, experiment, exp_data, setup)
        self.comps_sims_to_batch = int(self.get_property('sims_per_thread'))
        self.sims_to_create = []
        self.commissioners = []
        self.assets_service = self.setup.getboolean('use_comps_asset_svc')
        self.endpoint = self.setup.get('server_endpoint')
        self.compress_assets = self.setup.getboolean('compress_assets')

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
        return CompsSimulationCommissioner.create_suite(self.setup, suite_name)

    def create_experiment(self, experiment_name,experiment_id=None, suite_id=None):
        # Also create the experiment in COMPS to get the ID
        exp_id = CompsSimulationCommissioner.create_experiment(self.setup, self.config_builder,
                                                               experiment_name, self.staged_bin_path,
                                                               self.commandline.Options, suite_id)
        # Create experiment in the base class
        super(CompsExperimentManager, self).create_experiment(experiment_name, exp_id, suite_id)

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

        # Commission the batch if we filled it
        if len(self.sims_to_create) % self.comps_sims_to_batch == 0:
            # Acquire the semaphore
            self.maxThreadSemaphore.acquire()

            # Create a commissioner
            commissioner = CompsSimulationCommissioner(self.experiment.exp_id, self.maxThreadSemaphore, self.setup.get('server_endpoint'))

            # Add all the simulation
            for sim in self.sims_to_create:
                commissioner.create_simulation(sim)

            # Start the commission
            commissioner.start()

            # Add it to the list
            self.commissioners.append(commissioner)

    def complete_sim_creation(self):
        # Make sure all commissioners are done
        for c in self.commissioners:
            c.join()

        # collect the metadata
        for c in self.commissioners:
            for sim in c.created_simulations:
                if not self.experiment.contains_simulation(sim.id):
                    sim = DataStore.create_simulation(id=sim.id, tags=sim.tags)
                    self.experiment.simulations.append(sim)

    def commission_simulations(self, states):
        import threading
        from simtools.SimulationRunner.COMPSRunner import COMPSSimulationRunner
        t1 = threading.Thread(target=COMPSSimulationRunner, args=(self.experiment, states,self.success_callback, not self.done_commissioning()))
        t1.daemon = True
        t1.start()
        self.runner_created = True

    def cancel_experiment(self):
        utils.COMPS_login(self.endpoint)
        from COMPS.Data import Experiment, QueryCriteria
        e = Experiment.GetById(self.experiment.exp_id, QueryCriteria().Select('Id'))
        if e:
            e.Cancel()

    def hard_delete(self):
        """
        Delete local cache data for experiment and marks the server entity for deletion.
        """
        # Perform soft delete cleanup.
        self.soft_delete()

        # Mark experiment for deletion in COMPS.
        utils.COMPS_login(self.endpoint)
        from COMPS.Data import Experiment, QueryCriteria
        e = Experiment.GetById(self.experiment.exp_id, QueryCriteria().Select('Id'))
        e.Delete()

    def kill_simulation(self, sim_id):
        utils.COMPS_login(self.endpoint)
        from COMPS.Data import QueryCriteria, Simulation
        s = Simulation.GetById(sim_id, QueryCriteria().Select('Id'))
        s.Cancel()