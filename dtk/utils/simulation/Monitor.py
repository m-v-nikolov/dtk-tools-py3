import os           # mkdir, chdir, path, etc.
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

    def __init__(self, job_id, sim_dir=None):
        threading.Thread.__init__(self)
        self.msg = ""
        self.state = "Unknown"
        self.job_id = job_id
        self.sim_dir = sim_dir

    def run(self):
        try:
            jobids = psutil.get_pid_list()
        except NameError:
            print("Failed to import 'psutil' package.  Unable to query status of locally submitted simulations.")
            return self.state

        status_path = os.path.join(self.sim_dir, 'status.txt')
        if self.job_id in jobids and ('Eradication.exe' in psutil.Process(self.job_id).exe()):
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

# A class to monitor simulations on an HPC
class HpcSimulationMonitor(SimulationMonitor):

    def __init__(self, job_id, head_node):
        SimulationMonitor.__init__(self, job_id)
        self.head_node = head_node

    def run(self):
        monitor_cmd_line = "job view /scheduler:" + self.head_node + " " + str(self.job_id)
        #print( "Executing hpc_command_line: " + monitor_cmd_line )
        #print( "Checking status of job " + str(self.job_id) )
        hpc_pipe = subprocess.Popen( monitor_cmd_line.split(), shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE )
        [hpc_pipe_stdout, hpc_pipe_stderr] = hpc_pipe.communicate()
        #print(hpc_pipe_stdout, hpc_pipe_stderr)

        hpc_status = [tuple(l.split(':', 1)) for l in hpc_pipe_stdout.split('\n')]
        hpc_state_lookup = dict( [(t[0].strip(),t[1].strip()) for t in hpc_status if len(t) is 2] )

        self.state = hpc_state_lookup.get("State", "Unknown")
        self.msg = hpc_state_lookup.get("Progress Message", "")

# A class to monitor simulation through COMPS
class CompsSimulationMonitor(SimulationMonitor):

    def __init__(self, job_id, server_endpoint):
        SimulationMonitor.__init__(self, job_id)
        self.server_endpoint = server_endpoint

    def run(self):
        from COMPSJavaInterop import Client, Simulation, QueryCriteria
        
        Client.Login(self.server_endpoint)

        sims = Simulation.Get( QueryCriteria().Select('Id,SimulationState').Where('ExperimentId=' + self.job_id) )
        
        self.state = {}
        self.msg = {}
        for sim in sims.toArray():
            self.state[sim.getId().toString()] = sim.getState().toString()
            self.msg[sim.getId().toString()] = ''
