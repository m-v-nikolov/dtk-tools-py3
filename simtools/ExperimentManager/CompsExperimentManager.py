import os

from simtools import utils
from simtools.Commisioner import CompsSimulationCommissioner
from simtools.DataAccess.DataStore import DataStore
from simtools.ExperimentManager.BaseExperimentManager import BaseExperimentManager
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
        self.endpoint = self.setup.get('server_endpoint')
        self.compress_assets = self.setup.getboolean('compress_assets')

    def check_input_files(self, input_files):
        """
        Check file exist and return the missing files as dict
        """
        input_root = self.setup.get('input_root')
        input_root_real = utils.translate_COMPS_path(input_root)

        missing_files = {}
        for (filename, filepath) in input_files.iteritems():
            if isinstance(filepath, basestring):
                if not os.path.exists(os.path.join(input_root_real, filepath)):
                    missing_files[filename] = filepath
            elif isinstance(filepath, list):
                missing_files[filename] = [f for f in filepath if not os.path.exists(os.path.join(input_root_real, f))]
                # Remove empty list
                if len(missing_files[filename]) == 0:
                    missing_files.pop(filename)

        return missing_files

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

    def create_experiment(self, experiment_name, suite_id=None):
        self.sims_created = 0
        # Also create the experiment in COMPS to get the ID
        exp_id = CompsSimulationCommissioner.create_experiment(self.setup, self.config_builder,
                                                               experiment_name, self.staged_bin_path,
                                                               self.commandline.Options, suite_id)
        # Create experiment in the base class
        super(CompsExperimentManager, self).create_experiment(experiment_name, exp_id, suite_id)

        # Set some extra stuff
        self.experiment.endpoint = self.endpoint

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
        tags.update(self.exp_builder.tags if hasattr(self.exp_builder, 'tags') else {})
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

    def commission_simulations(self, states):
        import threading
        from simtools.SimulationRunner.COMPSRunner import COMPSSimulationRunner

        t1 = threading.Thread(target=COMPSSimulationRunner, args=(self.experiment, states,
                                                                  self.success_callback,
                                                                  not self.done_commissioning()))
        t1.daemon = True
        t1.start()
        self.runner_created = True

    def collect_sim_metadata(self):
        for simid, simdata in CompsSimulationCommissioner.get_sim_metadata_for_exp(self.experiment.exp_id).iteritems():
            # Only add simulation if not yet present in the experiment
            if not self.experiment.contains_simulation(simid):
                sim = DataStore.create_simulation(id=simid, tags=simdata)
                self.experiment.simulations.append(sim)

    def cancel_all_simulations(self, states=None):
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

    def kill_job(self, simId):
        utils.COMPS_login(self.endpoint)
        from COMPS.Data import QueryCriteria, Simulation
        s = Simulation.GetById(simId, QueryCriteria().Select('Id'))
        s.Cancel()
