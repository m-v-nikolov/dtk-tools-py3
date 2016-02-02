import os           # mkdir, path, etc.
import subprocess   # to execute command-line instructions
import threading    # for multi-threaded job submission and monitoring
import time         # for sleep
import re           # regular expressions
from datetime import datetime

from CommandlineGenerator import CommandlineGenerator # to construct command line strings from executable, options, and params

# A class to commission simulations locally
class SimulationCommissioner(threading.Thread):

    def __init__(self, sim_dir, eradication_command):
        threading.Thread.__init__(self)
        self.sim_dir = sim_dir
        self.eradication_command = eradication_command
        self.job_id = None
        self.sim_id = os.path.basename(self.sim_dir)

    def run(self):
        with open(os.path.join(self.sim_dir,"StdOut.txt"),"w") as out:
            with open(os.path.join(self.sim_dir,"StdErr.txt"),"w") as err:
                p = subprocess.Popen( self.eradication_command.Commandline.split(), 
                                      cwd=self.sim_dir, shell=False, stdout=out, stderr=err )
                self.job_id = p.pid

# A class to commission simulations through COMPS
class CompsSimulationCommissioner(SimulationCommissioner):

    def __init__(self, exp_id, maxThreadSemaphore):
        SimulationCommissioner.__init__(self, 'c:\\', None)
        self.exp_id = exp_id
        self.maxThreadSemaphore = maxThreadSemaphore
        self.sims = []

    @staticmethod
    def createExperiment(setup, config_builder, exp_name, bin_path, input_args):
        from COMPS import Client
        from COMPS.Data import Configuration, HPCJob__Priority, Experiment

        Client.Login(setup.get('HPC','server_endpoint'))

        bldr = Configuration.getBuilderInstance()
        config = bldr.setSimulationInputArgs(input_args) \
                     .setWorkingDirectoryRoot(os.path.join(setup.get('HPC','sim_root'), exp_name + '_' + re.sub( '[ :.-]', '_', str( datetime.now() ) ))) \
                     .setExecutablePath(bin_path) \
                     .setNodeGroupName(setup.get('HPC','node_group')) \
                     .setMaximumNumberOfRetries(int(setup.get('HPC', 'num_retries'))) \
                     .setPriority(HPCJob__Priority.valueOf(setup.get('HPC','priority'))) \
                     .setMinCores(config_builder.get_param('Num_Cores',1)) \
                     .setMaxCores(config_builder.get_param('Num_Cores',1)) \
                     .build()

        # print('exp_name - ' + str(exp_name))
        # print('config - ' + str(config))
        e = Experiment(exp_name, config)
        e.Save()
        return e.getId().toString()

    @staticmethod
    def commissionExperiment(exp_id):
        from COMPS.Data import Experiment

        e = Experiment.GetById(exp_id)
        e.Commission()

    @staticmethod
    def getSimMetadataForExp(exp_id):
        from COMPS.Data import Experiment, QueryCriteria

        e = Experiment.GetById(exp_id)
        sims = e.GetSimulations(QueryCriteria().Select('Id').SelectChildren('Tags')).toArray()
        sim_md = {}
        for sim in sims:
            md={}
            for tag in sim.getTags().entrySet().toArray():
                # COMPS turns nested tags into strings like "{'key':'value'}"
                try:
                    v=eval(tag.getValue())
                    #print('Converting string to value: %s' % v)
                except:
                    v=tag.getValue()
                md[tag.getKey()]=v
            sim_md[sim.getId().toString()] = md
        # print(sim_md)
        return sim_md

    def createSimulation(self, name, files, tags):
        sim = { 'name': name, 'tags': tags }
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

                s.AddFile(SimulationFile('config.json', 'input', 'The configuration file'), sim.pop('config'))
                s.AddFile(SimulationFile('campaign.json', 'input', 'The campaign file'), sim.pop('campaign'))
                s.AddFile(SimulationFile('emodules_map.json', 'input', 'Map of emodules used'), sim.pop('emodules'))
                for name,content in sim.items():
                    s.AddFile(SimulationFile('%s.json'%name, 'input', 'The %s configuration file'%name), content)

                # s.Save()    # not here... we'll batch save later...

            self.sims = []
            
            Simulation.SaveAll()
        finally:
            self.maxThreadSemaphore.release()