import multiprocessing
import os
import re
from datetime import datetime

import logging
import utils
from COMPS.Data import Configuration
from COMPS.Data import Experiment
from COMPS.Data import Priority
from COMPS.Data import QueryCriteria
from COMPS.Data import Simulation
from COMPS.Data import SimulationFile
from COMPS.Data import Suite

logger = logging.getLogger('Commissioner')


class CompsSimulationCommissioner(multiprocessing.Process):
    """
    A class to commission COMPS experiments and simulations.
    Threads are spawned for each batch submission of created simulation (and associated) objects.
    Commissioning and meta-data retrieval are done by single calls by passing the experiment ID.
    """

    def __init__(self, exp_id, maxThreadSemaphore, endpoint):
        multiprocessing.Process.__init__(self)
        self.exp_id = exp_id
        self.maxThreadSemaphore = maxThreadSemaphore
        self.endpoint = endpoint
        self.sims = []

    def create_simulation(self, name, files, tags):
        sim = {'name': name, 'tags': tags}
        sim.update(files)
        self.sims.append(sim)

    def run(self):
        utils.COMPS_login(self.endpoint)
        try:
            for sim in self.sims:
                # Create the simulation
                s = Simulation(name=sim.pop('name'), experiment_id=self.exp_id)

                # Sets the tags
                s.set_tags(sim.pop('tags'))

                # Add the files
                for name, content in sim.items():
                    s.add_file(simulationfile=SimulationFile(name, 'input'), data=content)

            Simulation.save_all()  # Batch save after all sims in list have been added

            self.sims = []

        finally:
            self.maxThreadSemaphore.release()

    @staticmethod
    def create_suite(setup, suite_name):
        utils.COMPS_login(setup.get('server_endpoint'))

        logger.debug('Suite_name - ' + str(suite_name))

        suite = Suite(suite_name)
        suite.save()

        return str(suite.id)

    @staticmethod
    def create_experiment(setup, config_builder, exp_name, bin_path, input_args, suite_id=None):
        utils.COMPS_login(setup.get('server_endpoint'))

        config = Configuration(
            environment_name=setup.get('environment'),
            simulation_input_args=input_args,
            working_directory_root=os.path.join(setup.get('sim_root'), exp_name + '_' + re.sub( '[ :.-]', '_', str( datetime.now() ) )),
            executable_path=bin_path,
            node_group_name=setup.get('node_group'),
            maximum_number_of_retries=int(setup.get('num_retries')),
            priority=Priority[setup.get('priority')],
            min_cores=config_builder.get_param('Num_Cores',1),
            max_cores=config_builder.get_param('Num_Cores',1),
            exclusive=config_builder.get_param('Exclusive',False)
        )

        logger.debug('exp_name - ' + str(exp_name))
        logger.debug('config - ' + str(config))

        e = Experiment(name=exp_name,
                       configuration=config,
                       suite_id=suite_id)
        e.save()

        return e.id

    @staticmethod
    def get_sim_metadata_for_exp(exp_id):
        e = Experiment.get(exp_id)
        sims = e.get_simulations(QueryCriteria().select('Id').select_children('Tags'))

        sim_md = {}
        for sim in sims:
            md = {}
            for tag,value in sim.tags.iteritems():
                md[tag] = value
            sim_md[str(sim.id)] = md
            logger.debug(sim_md)

        return sim_md
