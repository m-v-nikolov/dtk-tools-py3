from simtools import utils
from simtools.Commisioner import CompsSimulationCommissioner
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
from simtools.Monitor import CompsSimulationMonitor
from simtools.OutputParser import CompsDTKOutputParser


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
        self.commissioner = None
        self.sims_created = 0
        self.assets_service = self.setup.getboolean('use_comps_asset_svc')

    def get_monitor(self):
        return CompsSimulationMonitor(self.experiment.exp_id, self.experiment.suite_id, self.setup.get('server_endpoint'))

    def analyze_simulations(self):
        if not self.assets_service:
            CompsDTKOutputParser.createSimDirectoryMap(self.exp_data.get('exp_id'), self.exp_data.get('suite_id'))
        if self.setup.getboolean('compress_assets'):
            CompsDTKOutputParser.enableCompression()

        super(CompsExperimentManager, self).analyze_simulations()

    def create_suite(self, suite_name):
        return CompsSimulationCommissioner.create_suite(self.setup, suite_name)

    def create_experiment(self, experiment_name, suite_id=None):

        self.sims_created = 0
        # Also create the experiment in COMPS to get the ID
        exp_id = CompsSimulationCommissioner.create_experiment(self.setup, self.config_builder,
                                                               experiment_name, self.staged_bin_path,
                                                               self.commandline.Options, suite_id)
        # Create experiment in the base class
        super(CompsExperimentManager, self).create_experiment(experiment_name, exp_id, suite_id)

    def create_simulation(self):
        if self.sims_created % self.comps_sims_to_batch == 0:
            self.maxThreadSemaphore.acquire()  # Is this okay outside the thread?  Stops the thread from being created
            # until it can actually go, but asymmetrical acquire()/release() is not
            # ideal...

            self.commissioner = CompsSimulationCommissioner(self.experiment.exp_id, self.maxThreadSemaphore)
            ret = self.commissioner
        else:
            ret = None

        files = self.config_builder.dump_files_to_string()
        tags = self.exp_builder.metadata
        # Append the environment to the tag
        tags['environment'] = self.setup.get('environment')
        self.commissioner.create_simulation(self.config_builder.get_param('Config_Name'), files, tags)

        self.sims_created += 1

        if self.sims_created % self.comps_sims_to_batch == 0:
            self.commissioner.start()
            self.commissioner = None

        return ret

    def complete_sim_creation(self, commissioners):
        lastBatch = commissioners[-1]
        if not lastBatch.isAlive() and len(lastBatch.sims) > 0:
            lastBatch.start()
        for c in commissioners:
            c.join()
        self.collect_sim_metadata()

    def commission_simulations(self):
        CompsSimulationCommissioner.commission_experiment(self.experiment.exp_id)
        super(CompsExperimentManager, self).commission_simulations()
        return True

    def collect_sim_metadata(self):
        for simid, simdata in  CompsSimulationCommissioner.get_sim_metadata_for_exp(self.experiment.exp_id).iteritems():
            sim = DataStore.create_simulation(id=simid, tags=simdata)
            self.experiment.simulations.append(sim)

        DataStore.save_experiment(self.experiment)

    def cancel_all_simulations(self, states=None):
        utils.COMPS_login(self.get_property('server_endpoint'))
        from COMPS.Data import Experiment, QueryCriteria, Simulation
        e = Experiment.GetById(self.experiment.exp_id, QueryCriteria().Select('Id'))
        e.Cancel()

    def hard_delete(self):
        """
        Delete local cache data for experiment and marks the server entity for deletion.
        """
        # Perform soft delete cleanup.
        self.soft_delete()

        # Mark experiment for deletion in COMPS.
        utils.COMPS_login(self.get_property('server_endpoint'))
        from COMPS.Data import Experiment, QueryCriteria, Simulation
        e = Experiment.GetById(self.experiment.exp_id, QueryCriteria().Select('Id'))
        e.Delete()

    def kill_job(self, simId):
        utils.COMPS_login(self.get_property('server_endpoint'))
        from COMPS.Data import Experiment, QueryCriteria, Simulation
        s = Simulation.GetById(simId, QueryCriteria().Select('Id'))
        s.Cancel()
