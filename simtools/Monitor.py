import json
import logging
import os

try:
    import psutil  # for local PID lookup in SimulationStatus (external dependency: https://code.google.com/p/psutil/)
except:
    print("Unable to import 'psutil' package.  Will not be able to query status of locally submitted simulations.")
    pass

logger = logging.getLogger(__name__)

class SimulationMonitor(object):

    '''
    A class to monitor the status of local simulation.
    Threads are spawned to query each simulation in parallel.
    '''

    def __init__(self, exp_data, setup):
        self.exp_data = exp_data

    def query(self):
        states, msgs = {}, {}
        for sim_id, sim in self.exp_data['sims'].items():
            job_id = sim.get('jobId')
            if job_id:
                state, msg = self.query_sim(sim_id, job_id)
                states[job_id] = state
                msgs[job_id] = msg
        return states, msgs

    def query_sim(self, sim_id, job_id):

        state, msg = 'Unknown', ''
        job_running = False

        try:
            logger.debug('exe_name = %s', self.exp_data.get('exe_name'))
            logger.debug('job_id = %d, psutil.Process.name = %s', job_id, psutil.Process(job_id).name())
            job_running = (os.path.basename(self.exp_data.get('exe_name')).lower()
                           in psutil.Process(job_id).name().lower())
        except NameError:
            logger.warning("Failed to import 'psutil' package.  Unable to query status of locally submitted simulations.")
            return state, msg
        except psutil.AccessDenied:
            logger.warning('Access to process ID denied.')
        except psutil.NoSuchProcess:
            logger.debug('No such process with PID %d', job_id)

        status_path = os.path.join(self.exp_data['sim_root'],
                               '_'.join([self.exp_data['exp_name'], self.exp_data['exp_id']]),
                               sim_id, 'status.txt')

        if os.path.exists(status_path):
            with open(status_path, 'r') as status_file:
                msg = list(status_file)[-1]

        if job_running:
            state = 'Running'
        else:
            if msg:
                state = 'Finished' if 'Done' in msg else 'Canceled'
            else:
                state = 'Failed'

        return state, msg


class CompsSimulationMonitor(SimulationMonitor):

    '''
    A class to monitor the status of COMPS simulations.
    Note that only a single thread is spawned as the COMPS query is based on the experiment ID
    '''

    def __init__(self, exp_data, setup):
        self.exp_data = exp_data
        self.server_endpoint = setup.get('server_endpoint')

    def query(self):
        from COMPS import Client
        from COMPS.Data import Simulation, Experiment, Suite, QueryCriteria

        Client.Login(self.server_endpoint)

        def sims_from_experiment(e):
            logger.info('Monitoring simulations for ExperimentId = %s', e.getId().toString())
            return e.GetSimulations(QueryCriteria().Select('Id,SimulationState')).toArray()

        def sims_from_experiment_id(exp_id):
            e = Experiment.GetById(exp_id)
            return sims_from_experiment(e)

        def sims_from_suite_id(suite_id):
            logger.info('Monitoring simulations for SuiteId = %s', suite_id)
            s = Suite.GetById(suite_id)
            exps = s.GetExperiments(QueryCriteria().Select('Id')).toArray()
            sims = []
            for e in exps:
                sims += sims_from_experiment(e)
            return sims

        if 'suite_id' in self.exp_data:
            suite_id = self.exp_data['suite_id']
            sims = sims_from_suite_id(suite_id)
        elif 'exp_id' in self.exp_data:
            exp_id = self.exp_data['exp_id']
            sims = sims_from_experiment_id(exp_id)
        else:
            raise Exception('Unable to monitor COMPS simulations as metadata contains no Suite or Experiment ID:\n%s' % json.dumps(self.exp_data, indent=4))

        states, msgs = {}, {}
        for sim in sims:
            id_string = sim.getId().toString()
            states[id_string] = sim.getState().toString()
            msgs[id_string] = ''

        return states, msgs
