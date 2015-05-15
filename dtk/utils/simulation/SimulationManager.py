from ConfigParser import ConfigParser  # to parse dtk_setup.cfg
from datetime import datetime          # for unique sim_id
from hashlib import md5                # for re-use of identical Eradication.exe
from collections import Counter        # for concise job-state status during batching
import os                              # mkdir, chdir, path, kill, etc.
import json                            # for dumping metadata
import re                              # for regex substitutions
import shutil                          # for file copy
import signal                          # for killing local jobs
import subprocess                      # to execute command-line instructions
import time                            # for sleep
import copy                            # for cached DTKConfigBuilder object
import warnings
import threading

import logging
logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

from CommandlineGenerator import CommandlineGenerator # for command line strings: executable, options, and params
from ..core.DTKSetupParser import DTKSetupParser      # to parse user-specific setup
from ..builders.sweep import DefaultSweepBuilder  # default builder runs single simulation

from Commisioner import SimulationCommissioner, HpcSimulationCommissioner, CompsSimulationCommissioner
from Monitor import SimulationMonitor, HpcSimulationMonitor, CompsSimulationMonitor
from OutputParser import DTKOutputParser, CompsDTKOutputParser

def getMd5FromFile(filename):
    logger.info('Getting md5 for ' + filename)
    with open(filename) as dtk_file:
        md5calc = md5()
        while True:
            dtk_data = dtk_file.read(10240) # value picked from example!
            if len(dtk_data) == 0:
                break
            md5calc.update(dtk_data)
    dtk_md5 = md5calc.hexdigest()
    return dtk_md5

class SimulationManagerFactory():
    @staticmethod
    def factory(type):
        if type == 'LOCAL':
            return LocalSimulationManager
        if type == 'HPC':
            return CompsSimulationManager
        if type == 'HPC-OLD': 
            warnings.warn("The 'HPC-OLD' flag for direct HPC submission by 'job submit' is being removed in favor of COMPS submission.", DeprecationWarning)
            return HpcSimulationManager
        raise Exception("SimulationManagerFactory location argument should be either 'LOCAL' or 'HPC'.")

    @classmethod
    def from_exe(cls,exe_path, location='LOCAL'):
        if not exe_path:
            raise Exception('SimulationManagerFactory.from_exe takes the executable path as an argument.')
        return cls.factory(location)(exe_path, {})

    @classmethod
    def from_file(cls,exp_data_path):
        logger.info('Loading SimulationManagerFactory.from_file: ' + exp_data_path)
        with open(exp_data_path) as exp_data_file:
            exp_data = json.loads(exp_data_file.read())
        return cls.factory(exp_data['location'])('', exp_data)

class LocalSimulationManager():
    '''
    Manages the creation, submission, status, parsing, and analysis of local DTK simulations
    '''

    def __init__(self, exe_path, exp_data):
        self.location  = 'LOCAL'
        self.exp_data  = exp_data
        self.exe_path  = exe_path
        self.setup     = DTKSetupParser()
        self.emodules  = []
        self.analyzers = []

    def RunSimulations(self, config_builder, exp_name='test', exp_builder=DefaultSweepBuilder(), show_progress=False):

        self.exp_name = exp_name
        self.config_builder = config_builder
        self.exp_builder = exp_builder

        sim_root = self.getProperty('sim_root')
        bin_root = self.getProperty('bin_root')
        dll_root = self.getProperty('dll_root')

        self.bin_path = self.StageExecutable(bin_root)
        self.emodules.extend(list(config_builder.dlls))
        self.emodules_map = self.StageEmodules(dll_root)

        input_path = self.getProperty('input_root')

        eradication_options = { '--config':'config.json', '--input-path':input_path }
        if show_progress: 
            eradication_options['--progress'] = ''
        self.eradication_command = CommandlineGenerator(self.bin_path, eradication_options, [])

        self.getExperimentId()

        logger.info("Creating exp_id = " + self.exp_id)
        sim_path = os.path.join(sim_root, exp_name + '_' + self.exp_id)
        self.exp_data.update({'sim_root': sim_root, 
                              'exp_name': exp_name, 
                              'exp_id': self.exp_id,
                              'location': self.location, 
                              'sim_type': self.config_builder.get_param('Simulation_Type')})

        sims = []
        self.exp_data['sims'] = {}
        cache_cwd = os.getcwd()
        self.doLocalBatching = False

        # Cache original config_builder for exp_builder to alter
        cached_cb = copy.deepcopy(self.config_builder)

        for mod_fn_list in self.exp_builder.mod_generator:
     
            # reset to base config/campaign
            self.config_builder = copy.deepcopy(cached_cb)

            # modify next simulation according to experiment builder
            for mod_fn in mod_fn_list:
                mod_fn(self.config_builder)

            commissioned = self.commissionSimulation(sim_path,sims)
            if not commissioned: 
                break

        if not self.commissioner.isAlive():
            self.commissioner.start() # e.g. last accumulated COMPS batch

        # join threads before proceeding
        for s in sims:
            s.join()

        # collect information on submitted simulations
        self.collectSimMetaData(sims)
        
        # dump experiment data to output
        os.chdir(cache_cwd)
        if not os.path.exists('simulations'):
            os.mkdir('simulations')
        with open(os.path.join('simulations', exp_name + '_' + self.exp_id + '.json'), 'w') as exp_file:
            logger.info('Saving meta-data for experiment:')
            logger.info(json.dumps(self.exp_data, sort_keys=True, indent=4))
            logger.info(os.getcwd())
            exp_file.write(json.dumps(self.exp_data, sort_keys=True, indent=4))

    def getExperimentId(self):
        self.exp_id = re.sub('[ :.-]', '_', str(datetime.now()))

    def createSimulation(self, sim_path):
        time.sleep(0.01) # just in case?
        sim_id = re.sub('[ :.-]', '_', str(datetime.now()))
        logger.debug('Creating sim_id = ' + sim_id)
        sim_dir = os.path.join(sim_path, sim_id)
        os.makedirs(sim_dir)
        self.config_builder.dump_files(sim_dir)
        with open(os.path.join(sim_dir, 'emodules_map.json'), 'w') as emodules_file:
            emodules_file.write(json.dumps(self.emodules_map, sort_keys=True, indent=4))
        return sim_dir

    def commissionSimulation(self, sim_path, sims):
        # create simulation directory and populate with configuration files
        sim_dir = self.createSimulation(sim_path)

        max_local_sims = int(self.setup.get('LOCAL', 'max_local_sims'))
        if len(sims) == max_local_sims:
            warnings.warn("Trying to submit more than %d concurrent local simulations." % max_local_sims, Warning)
            choice = raw_input('Do you want to continue?  Yes [Y], Batch [B], No [N]...')
            if choice.lower() == 'y':
                logger.info('Continuing all in parallel...')
            elif choice.lower() == 'b':
                logger.info('Batching...')
                self.doLocalBatching = True
            else:
                logger.info('Truncating...')
                return False

        if self.doLocalBatching:
            while True:
                for s in sims:
                    s.join()
                for s in sims:
                    self.exp_data['sims'][s.sim_id]['jobId'] = s.job_id
                states, msgs = self.SimulationStatus()
                running_ids = [ id for (id, state) in states.iteritems() if state in ['Running'] ]
                if len(running_ids) >= max_local_sims:
                    logger.info(dict(Counter(states.values())))
                    time.sleep(10)
                else:
                    break

        self.commissioner = SimulationCommissioner(sim_dir, self.eradication_command)

        # store meta-data related to experiment builder for each sim
        self.exp_data['sims'][self.commissioner.sim_id] = self.exp_builder.metadata

        # submit simulation
        self.commissioner.start()
        sims.append(self.commissioner)
        return True

    def collectSimMetaData(self,sims):
        for s in sims:
            self.exp_data['sims'][s.sim_id]['jobId'] = s.job_id

    def SimulationStatus(self):
        logger.debug("Status of simulations run on '%s':" % self.location)

        monitors = []
        for (sim_id, sim) in self.exp_data['sims'].items():
            job_id = sim['jobId']
            monitor = self.getSimulationMonitor(sim_id, job_id)
            monitor.start()
            monitors.append(monitor)

        for m in monitors:
            m.join()

        states = {}
        msgs = {}
        for m in monitors:
            states[m.job_id] = m.state
            msgs[m.job_id] = m.msg
        return states, msgs

    @staticmethod
    def printStatus(states,msgs):
        # A bit more verbose if there are status messages
        long_states = copy.deepcopy(states)
        for jobid,state in states.items():
            if 'Running' in state:
                steps_complete = [int(s) for s in msgs[jobid].split() if s.isdigit()]
                if len(steps_complete) == 2:
                    long_states[jobid] += " (" + str(100*steps_complete[0]/steps_complete[1]) + "% complete)"

        print('Job states:')
        print( json.dumps(long_states, sort_keys=True, indent=4) )
        print( dict(Counter(states.values())) )

    @staticmethod
    def statusFinished(states):
        return all(v in ['Finished', 'Succeeded', 'Failed', 'Canceled'] for v in states.itervalues())

    def getSimulationMonitor(self, sim_id, job_id):
        sim_dir = os.path.join(self.exp_data['sim_root'], 
                               '_'.join((self.exp_data['exp_name'],
                                         self.exp_data['exp_id'])),
                               sim_id)
        return SimulationMonitor(job_id, sim_dir)

    def ResubmitSimulations(self, ids=[], resubmit_all_failed=False):
        states, msgs = self.SimulationStatus()
        if resubmit_all_failed:
            ids = [ id for (id, state) in states.iteritems() if state in ['Failed','Canceled'] ]
            logger.info('Resubmitting all failed simulations in experiment: ' + str(ids))
        for id in ids:
            state = states.get(id)
            if not state:
                logger.warning('No job in current experiment with ID = %s' % id)
                continue
            if state in ['Failed', 'Canceled']:
                self.resubmitJob(id)
            else:
                logger.warning("JobID %d is in a '%s' state and will not be requeued." % (id,state))

    def resubmitJob(self, job_id):
        logger.warning('Not yet implemented for %s jobs' % self.location)

    def CancelSimulations(self, ids=[], killall=False):
        states, msgs = self.SimulationStatus()
        if killall:
            self.cancelAllSimulations(states)
            return
        for id in ids:
            state = states.get(id)
            if not state:
                logger.warning('No job in current experiment with ID = %s' % id)
                continue
            if state not in ['Finished', 'Succeeded', 'Failed', 'Canceled', 'Unknown']:
                self.killJob(id)
            else:
                logger.warning("JobID %s is already in a '%s' state." % (str(id),state))

    def cancelAllSimulations(self,states):
        ids = states.keys()
        logger.info('Killing all simulations in experiment: ' + str(ids))
        self.CancelSimulations(ids)

    def killJob(self, job_id):
        os.kill(job_id, signal.SIGTERM)

    def AnalyzeSimulations(self):
        parsers = {}

        for (sim_id, sim) in self.exp_data['sims'].items():

            # pass filtered analyses for this sim to its own threaded parser
            filtered_analyses = [a for a in self.analyzers if a.filter(sim)]
            if not filtered_analyses:
                logger.debug('Simulation did not pass filter on any analyzer.')
                continue

            parser = self.getOutputParser(sim_id, filtered_analyses)
            parser.start()
            parsers[parser.sim_id] = parser

        for p in parsers.values():
            p.join()

        if not parsers:
            logger.warn('No simulations passed analysis filters.')
            return

        for a in self.analyzers:
            a.combine(parsers)
            a.finalize()

    def getOutputParser(self, sim_id, filtered_analyses):
        return DTKOutputParser(os.path.join(self.exp_data['sim_root'],
                                            self.exp_data['exp_name'] + '_' + self.exp_data['exp_id']),
                               sim_id,
                               self.exp_data['sims'][sim_id],
                               filtered_analyses)

    def StageExecutable(self, bin_root):
        dtk_hash = getMd5FromFile(self.exe_path)
        logger.info('MD5 of ' + os.path.basename(self.exe_path) + ': ' + dtk_hash)
        bin_dir = os.path.join(bin_root, dtk_hash)
        bin_path = os.path.join(bin_dir, os.path.basename(self.exe_path))
        if not os.path.exists(bin_dir):
            try:
                os.makedirs(bin_dir)
            except:
                raise Exception("Unable to create directory: " + bin_dir)
        if not os.path.exists(bin_path):
            logger.info('Copying ' + os.path.basename(self.exe_path) + ' to ' + bin_dir + '...')
            shutil.copy(self.exe_path, bin_path)
            logger.info('Copying complete.')
        self.config_builder.set_param('bin_path', bin_path)
        return bin_path

    def StageEmodules(self, dll_root):
        tt = {'interventions':'interventions', 'disease_plugins':'diseases', 'reporter_plugins':'reporter_plugins'}
        emodules_map = {'interventions':[], 'diseases':[], 'reporter_plugins':[]}
        for emodule in self.emodules:
            logger.debug(emodule)
            (head, emodule_name) = os.path.split(emodule)
            (head, emodule_type) = os.path.split(head)
            emodule_hash = getMd5FromFile(emodule)
            emodule_dir = os.path.join(dll_root, emodule_type, emodule_hash)
            emodule_path = os.path.join(emodule_dir, emodule_name)
            logger.debug(emodule_path)
            emodules_map[tt[emodule_type]].append(emodule_path)
            if not os.path.exists(emodule_dir):
                try:
                    os.makedirs(emodule_dir)
                except:
                    logger.warning("Unable to create directory: " + emodule_dir)
            if not os.path.exists(emodule_path):
                logger.info('Copying ' + emodule_name + ' to ' + emodule_dir + '...')
                shutil.copy(emodule, emodule_path)
                logger.info('Copying complete.')
        logger.info('EMODules map: ' + str(emodules_map))
        return emodules_map

    def AddAnalyzer(self, analyzer):
        self.analyzers.append(analyzer)

    def getProperty(self,property):
        return self.setup.get(self.location,property)

class HpcSimulationManager(LocalSimulationManager):
    '''
    Extends the LocalSimulationManager to manage DTK simulations through direct HPC commands
    e.g. job submit, job view
    '''
    def __init__(self, exe_path, exp_data):
        LocalSimulationManager.__init__(self,exe_path,exp_data)
        self.location = 'HPC-OLD'

    def commissionSimulation(self, sim_path, sims):
        sim_dir = self.createSimulation(sim_path)

        logger.debug('Commissioning HPC simulation(s)...')
        config_name = self.config_builder.get_param('Config_Name')[:79]
        num_cores = self.config_builder.get_param('Num_Cores')
        self.commissioner = HpcSimulationCommissioner(sim_dir, 
                                        self.eradication_command, 
                                        self.setup, 
                                        config_name, 
                                        num_cores)

        # store meta-data related to experiment builder for each sim
        self.exp_data['sims'][self.commissioner.sim_id] = self.exp_builder.metadata

        # submit simulation
        self.commissioner.start()
        sims.append(self.commissioner)
        return True

    def getSimulationMonitor(self, sim_id, job_id):
        return HpcSimulationMonitor(job_id, self.getProperty('head_node'))

    def resubmitJob(self, job_id):
        resubmit_cmd_line = "job requeue " + str(job_id) + " /scheduler:" + self.getProperty('head_node')
        hpc_pipe = subprocess.Popen(resubmit_cmd_line.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        [hpc_pipe_stdout, hpc_pipe_stderr] = hpc_pipe.communicate()

    def killJob(self, job_id):
        logger.debug('Killing HPC simulations by job ID...')
        cancel_cmd_line = "job cancel " + str(job_id) + " /scheduler:" + self.getProperty('head_node')
        logger.debug("Executing hpc_command_line: " + cancel_cmd_line)
        logger.debug("Canceling job " + str(job_id))
        hpc_pipe = subprocess.Popen(cancel_cmd_line.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        [hpc_pipe_stdout, hpc_pipe_stderr] = hpc_pipe.communicate()
        logger.debug(hpc_pipe_stdout)
        logger.debug(hpc_pipe_stderr)

class CompsSimulationManager(LocalSimulationManager):
    '''
    Extends the LocalSimulationManager to manage DTK simulations through COMPS wrappers
    e.g. creation of Simulation, Experiment, Suite objects
    '''
    def __init__(self, exe_path, exp_data):
        LocalSimulationManager.__init__(self,exe_path,exp_data)
        self.location = 'HPC'
        self.comps_logged_in = False

    def getExperimentId(self):
        self.exp_id = CompsSimulationCommissioner.createExperiment(self.setup, self.config_builder, self.exp_name, self.bin_path, self.eradication_command.Options)
        self.sims_created = 0
        self.comps_sims_to_batch = int(self.getProperty('sims_per_thread'))
        self.maxThreadSemaphore = threading.Semaphore(int(self.getProperty('max_threads')))

    def createSimulation(self, sim_path):
        files = self.config_builder.dump_files_to_string()
        files.update({'emodules':json.dumps(self.emodules_map, sort_keys=True, indent=4)})
        tags = self.exp_builder.metadata
        self.commissioner.createSimulation(self.config_builder.get_param('Config_Name'), files, tags)

    def commissionSimulation(self, sim_path, sims):
        if self.sims_created % self.comps_sims_to_batch == 0:
            self.maxThreadSemaphore.acquire()    # Is this okay outside the thread?  Stops the thread from being created
                                                 # until it can actually go, but
                                                 # asymmetrical
                                                                                              # acquire()/release() is not
                                                                                              # ideal...
            self.commissioner = CompsSimulationCommissioner(self.exp_id, self.maxThreadSemaphore)
            sims.append(self.commissioner)

        # create simulation in COMPS
        self.createSimulation(sim_path)
        self.sims_created = self.sims_created + 1

        if self.sims_created % self.comps_sims_to_batch == 0:
            logger.debug('starting thread ' + str(len(sims)))
            self.commissioner.start()
        return True

    # TODO: rename function if this is doing the commissioning!
    def collectSimMetaData(self, sims):
        CompsSimulationCommissioner.commissionExperiment(self.exp_id)
        self.exp_data['sims'] = CompsSimulationCommissioner.getSimMetadataForExp(self.exp_id)

    def SimulationStatus(self):
        logger.debug("Status of simulations run on '%s':" % self.location)
        m = self.getSimulationMonitor(self.exp_data['exp_id'], self.exp_data['exp_id'])
        m.start()
        m.join()
        return m.state,m.msg

    def getSimulationMonitor(self, sim_id, job_id):
        return CompsSimulationMonitor(job_id, self.getProperty('server_endpoint'))

    def cancelAllSimulations(self,states):
        from COMPSJavaInterop import Client, Experiment, QueryCriteria

        Client.Login(self.setup.get('HPC','server_endpoint'))

        e = Experiment.GetById(self.exp_data['exp_id'], QueryCriteria().Select('Id'))
        e.Cancel()

    def killJob(self, job_id):
        from COMPSJavaInterop import Client, Simulation, QueryCriteria

        if not self.comps_logged_in:
            Client.Login(self.getProperty('server_endpoint'))
            self.comps_logged_in = True

        s = Simulation.GetById(job_id, QueryCriteria().Select('Id'))
        s.Cancel()

    def AnalyzeSimulations(self):
        self.sim_dir_map = CompsDTKOutputParser.createSimDirectoryMap(self.exp_data['exp_id'])
        LocalSimulationManager.AnalyzeSimulations(self)

    def getOutputParser(self, sim_id, filtered_analyses):
        return CompsDTKOutputParser(self.sim_dir_map,
                                    os.path.join(self.exp_data['sim_root'],
                                                 self.exp_data['exp_name'] + '_' + self.exp_data['exp_id']),
                                    sim_id,
                                    self.exp_data['sims'][sim_id],
                                    filtered_analyses)