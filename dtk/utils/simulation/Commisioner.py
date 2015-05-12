import os           # mkdir, chdir, path, etc.
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
        os.chdir(self.sim_dir)
        with open("StdOut.txt","w") as out:
            with open("StdErr.txt","w") as err:
                p = subprocess.Popen( self.eradication_command.Commandline.split(), 
                                      shell=False, stdout=out, stderr=err )
                self.job_id = p.pid
                time.sleep(3)
                #print('Process ID: ' + str(p.pid))

# A class to commission simulations to an HPC
class HpcSimulationCommissioner(SimulationCommissioner):

    def __init__(self, sim_dir, eradication_command, setup, config_name, numcores):
        SimulationCommissioner.__init__(self, sim_dir, eradication_command)
        self.setup = setup
        self.config_name = config_name
        if not numcores:
            print("config.json didn't contain 'Num_Cores' parameter.  Defaulting to one.")
            numcores = 1
        self.numcores = numcores

    def run(self):
        #mpiexec commandline
        mpi_bin = 'mpiexec'
        mpi_options = {}
        mpi_params = [self.eradication_command.Commandline]
        mpi_command = CommandlineGenerator(mpi_bin, mpi_options, mpi_params)

        #job submit commandline
        jobsubmit_bin = 'job submit'
        jobsubmit_options = { '/workdir:'  : self.sim_dir,
                              '/scheduler:': self.setup.get('HPC-OLD','head_node'),
                              '/nodegroup:': self.setup.get('HPC-OLD','node_group'),
                              '/user:'     : self.setup.get('HPC-OLD','username'),
                              '/jobname:'  : self.config_name,
                              '/numcores:' : str(self.numcores),
                              '/stdout:'   : 'StdOut.txt',
                              '/stderr:'   : 'StdErr.txt',
                              '/priority:' : self.setup.get('HPC-OLD','priority') }

        hpc_pwd = self.setup.get('HPC-OLD','password')
        if hpc_pwd:
            jobsubmit_options['/password:'] = hpc_pwd

        jobsubmit_params = [mpi_command.Commandline]
        jobsubmit_command = CommandlineGenerator(jobsubmit_bin, jobsubmit_options, jobsubmit_params)

        hpc_command_line = jobsubmit_command.Commandline
        #print("Executing hpc_command_line: " + hpc_command_line + '\n')
        p = subprocess.Popen( hpc_command_line.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        [hpc_pipe_stdout, hpc_pipe_stderr] = p.communicate()
        #print("Trying to read hpc response...")
        #print(hpc_pipe_stdout)

        if p.returncode == 0:
            job_id = hpc_pipe_stdout.split( ' ' )[-1].strip().rstrip('.')
            if str.isdigit(job_id) and job_id > 0:
                print( self.config_name + " submitted (as job_id " + str(job_id) + ")\n" )
                self.job_id = int(job_id)
            else:
                print( "ERROR: Job did not receive Id from HPC:\n" )
                print( hpc_pipe_stdout )
                print( hpc_pipe_stderr )
                return
        else:
            print( "ERROR: job submit of " + self.config_name + " failed!" )
            print( hpc_pipe_stdout )
            print( hpc_pipe_stderr )

# A class to commission simulations through COMPS
class CompsSimulationCommissioner(SimulationCommissioner):

    def __init__(self, exp_id, maxThreadSemaphore):
        SimulationCommissioner.__init__(self, 'c:\\', None)
        self.exp_id = exp_id
        self.maxThreadSemaphore = maxThreadSemaphore
        self.sims = []

    @staticmethod
    def createExperiment(setup, config_builder, exp_name, bin_path, input_args):
        from COMPSJavaInterop import Client, Configuration, Priority, Experiment

        Client.Login(setup.get('HPC','server_endpoint'))

        bldr = Configuration.getBuilderInstance();
        config = bldr.setSimulationInputArgs(input_args) \
                     .setWorkingDirectoryRoot(os.path.join(setup.get('HPC','sim_root'), exp_name + '_' + re.sub( '[ :.-]', '_', str( datetime.now() ) ))) \
                     .setExecutablePath(bin_path) \
                     .setNodeGroupName(setup.get('HPC','node_group')) \
                     .setMaximumNumberOfRetries(int(setup.get('HPC', 'num_retries'))) \
                     .setPriority(Priority.valueOf(setup.get('HPC','priority'))) \
                     .setMinCores(config_builder.get_param('Num_Cores',1)) \
                     .setMaxCores(config_builder.get_param('Num_Cores',1)) \
                     .build();

        # print('exp_name - ' + str(exp_name))
        # print('config - ' + str(config))
        e = Experiment(exp_name, config)
        e.Save()
        return e.getId().toString()

    @staticmethod
    def commissionExperiment(exp_id):
        from COMPSJavaInterop import Experiment

        e = Experiment.GetById(exp_id)
        e.Commission()

    @staticmethod
    def getSimMetadataForExp(exp_id):
        from COMPSJavaInterop import Experiment, QueryCriteria

        e = Experiment.GetById(exp_id)
        sims = e.GetSimulations(QueryCriteria().Select('Id').SelectChildren('Tags')).toArray()
        sim_md = {sim.getId().toString() : { tag.getKey() : tag.getValue() for tag in sim.getTags().entrySet().toArray() } for sim in sims}
        # print(sim_md)
        return sim_md

    def createSimulation(self, name, files, tags):
        sim = { 'name': name, 'tags': tags }
        sim.update(files)
        self.sims.append(sim)

    def run(self):
        from COMPSJavaInterop import Simulation, SimulationFile, autoclass

        try:
            for sim in self.sims:
                s = Simulation(sim.pop('name'))
                s.setExperimentId(self.exp_id)

                m = autoclass('java.util.HashMap')()
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
            
            # threading issues on the server side... don't commission now, we'll do it on the main thread (by calling commissionExperiment()) instead
            # e = Experiment.GetById(self.exp_id)
            # e.Commission()
        finally:
            self.maxThreadSemaphore.release()