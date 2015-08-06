import os           # mkdir, path, etc.
import json
import subprocess   # to execute command-line instructions
import threading    # for multi-threaded job submission and monitoring

# for local PID lookup in SimulationStatus (external dependency: https://code.google.com/p/psutil/)
try:
    import psutil
except:
    print("Unable to import 'psutil' package.  Will not be able to query status of locally submitted simulations.")
    pass

# A class to monitor simulations locally
class SimulationMonitor(threading.Thread):

    def __init__(self, job_id=None, sim_dir=None):
        threading.Thread.__init__(self)
        self.msg = ""
        self.state = "Unknown"
        self.job_id = job_id
        self.sim_dir = sim_dir

    def run(self):
        try:
            job_running = ('Eradication.exe' in psutil.Process(self.job_id).exe())
        except NameError:
            print("Failed to import 'psutil' package.  Unable to query status of locally submitted simulations.")
            return self.state
        except psutil.AccessDenied:
            print("Access to process ID denied.")
            job_running = False
        except psutil.NoSuchProcess:
            job_running = False

        status_path = os.path.join(self.sim_dir, 'status.txt')
        if job_running:
            self.state = 'Running'
            if os.path.exists(status_path):
                with open(status_path) as status_file:
                    self.msg = list(status_file)[-1]
        else:
            if os.path.exists(status_path):
                with open(status_path) as status_file:
                    #print(list(status_file)[-1])
                    if 'Done' in list(status_file)[-1]:
                        self.state = 'Finished'
                    else:
                        self.state = 'Canceled'
            else:
                self.state = 'Failed'

# A class to monitor simulation through COMPS

class CompsSimulationMonitor(SimulationMonitor):

    def __init__(self, exp_data, server_endpoint):
        SimulationMonitor.__init__(self)
        self.server_endpoint = server_endpoint
        self.exp_data = exp_data

    def run(self):
        from COMPS import Client
        from COMPS.Data import Simulation, Experiment, Suite, QueryCriteria

        Client.Login(self.server_endpoint)

        def sims_from_experiment(e):
            print('Monitoring simulations for ExperimentId = %s' % e.getId().toString())
            return e.GetSimulations(QueryCriteria().Select('Id,SimulationState')).toArray()

        def sims_from_experiment_id(exp_id):
            e = Experiment.GetById(exp_id)
            return sims_from_experiment(e)

        def sims_from_suite_id(suite_id):
            print('Monitoring simulations for SuiteId = %s' % suite_id)
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

        self.state = {}
        self.msg = {}
        for sim in sims:
            self.state[sim.getId().toString()] = sim.getState().toString()
            self.msg[sim.getId().toString()] = ''
