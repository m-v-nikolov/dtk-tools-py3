import logging
import os
import re
import threading
from datetime import datetime

import utils


class CompsSimulationCommissioner(threading.Thread):
    """
    A class to commission COMPS experiments and simulations.
    Threads are spawned for each batch submission of created simulation (and associated) objects.
    Commissioning and meta-data retrieval are done by single calls by passing the experiment ID.
    """

    def __init__(self, exp_id, maxThreadSemaphore):
        threading.Thread.__init__(self)
        self.exp_id = exp_id
        self.maxThreadSemaphore = maxThreadSemaphore
        self.sims = []

    def create_simulation(self, name, files, tags):
        sim = {'name': name, 'tags': tags}
        sim.update(files)
        self.sims.append(sim)

    def run(self):

        from COMPS.Data import Simulation, SimulationFile
        from java.util import HashMap

        try:
            for sim in self.sims:
                s = Simulation(sim.pop('name'))
                s.setExperimentId(self.exp_id)

                m = HashMap()
                for k,v in sim.pop('tags').items():
                    m.put(str(k), str(v))
                s.SetTags(m)

                for name, content in sim.items():
                    s.AddFile(SimulationFile('%s' % name, 'input', 'The %s configuration file' % name), content)

            Simulation.SaveAll()  # Batch save after all sims in list have been added
            self.sims = []

        finally:
            self.maxThreadSemaphore.release()

    @staticmethod
    def create_suite(setup, suite_name):

        from COMPS.Data import Suite
        utils.COMPS_login(setup.get('server_endpoint'))

        logging.debug('suite_name - ' + str(suite_name))

        suite = Suite(suite_name)
        suite.Save()

        return suite.getId().toString()

    @staticmethod
    def create_experiment(setup, config_builder, exp_name, bin_path, input_args, suite_id=None):
        from COMPS.Data import Configuration, HPCJob__Priority, Experiment

        utils.COMPS_login(setup.get('server_endpoint'))

        bldr = Configuration.getBuilderInstance()

        # When new version of pyCOMPS
        config = bldr.setSimulationInputArgs(input_args) \
                     .setWorkingDirectoryRoot(os.path.join(setup.get('sim_root'), exp_name + '_' + re.sub( '[ :.-]', '_', str( datetime.now() ) ))) \
                     .setExecutablePath(bin_path) \
                     .setNodeGroupName(setup.get('node_group')) \
                     .setMaximumNumberOfRetries(int(setup.get('num_retries'))) \
                     .setPriority(HPCJob__Priority.valueOf(setup.get('priority'))) \
                     .setMinCores(config_builder.get_param('Num_Cores',1)) \
                     .setMaxCores(config_builder.get_param('Num_Cores',1)) \
                     .setEnvironmentName(setup.get('environment')) \
                     .build()

        logging.debug('exp_name - ' + str(exp_name))
        logging.debug('config - ' + str(config))

        e = Experiment(exp_name, config)
        if suite_id:
            e.setSuiteId(suite_id)
        e.Save()

        return e.getId().toString()

    @staticmethod
    def commission_experiment(exp_id):

        from COMPS.Data import Experiment

        e = Experiment.GetById(exp_id)
        e.Commission()

    @staticmethod
    def get_sim_metadata_for_exp(exp_id):

        from COMPS.Data import Experiment, QueryCriteria

        e = Experiment.GetById(exp_id)
        sims = e.GetSimulations(QueryCriteria().Select('Id').SelectChildren('Tags')).toArray()

        sim_md = {}
        for sim in sims:
            md={}
            for tag in sim.getTags().entrySet().toArray():
                # COMPS turns nested tags into strings like "{'key':'value'}"
                try:
                    v = eval(tag.getValue())
                    # logging.debug('Converting string to value: %s' % v)
                except:
                    v = tag.getValue()
                md[tag.getKey()]=v
            sim_md[sim.getId().toString()] = md
        logging.debug(sim_md)

        return sim_md
