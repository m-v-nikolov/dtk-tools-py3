import os
import shlex
import subprocess
import time

from simtools.DataAccess.DataStore import DataStore
from simtools.SimulationRunner.BaseSimulationRunner import BaseSimulationRunner
from simtools.Utilities.General import init_logging, is_running
logger = init_logging("LocalRunner")
from COMPS.Data.Simulation import SimulationState

class LocalSimulationRunner(BaseSimulationRunner):
    """
    Run one simulation.
    """
    def __init__(self, simulation, experiment, thread_queue, states, success):
        super(LocalSimulationRunner, self).__init__(experiment, states, success)
        self.queue = thread_queue # used to limit the number of concurrently running simulations
        self.simulation = simulation
        self.sim_dir = self.simulation.get_path()

        if self.check_state() == SimulationState.CommissionRequested.value:
            self.run()
        else:
            self.queue.get()
            if self.simulation.status not in (SimulationState.Failed.value, SimulationState.Succeeded.value, SimulationState.Canceled.value):
                self.monitor()

    def run(self):
        try:
            with open(os.path.join(self.sim_dir, "StdOut.txt"), "w") as out, open(os.path.join(self.sim_dir, "StdErr.txt"), "w") as err:
                # On windows we want to pass the command to popen as a string
                # On Unix, we want to pass it as a sequence
                # See: https://docs.python.org/2/library/subprocess.html#subprocess.Popen
                if os.name == "nt":
                    command = self.experiment.command_line
                else:
                    command = shlex.split(self.experiment.command_line)

                # Launch the command
                p = subprocess.Popen(command, cwd=self.sim_dir, shell=False, stdout=out, stderr=err)

                # We are now running
                self.simulation.pid = p.pid
                self.simulation.status = SimulationState.Running.value
                self.update_status()

            self.monitor()
        except Exception as e:
            print "Error encountered while running the simulation."
            print e
        finally:
            # Allow another different thread to run now that this one is done.
            self.queue.get()

    def monitor(self):
        # Wait the end of the process
        # We use poll to be able to update the status

        while is_running(self.simulation.pid, name_part='Eradication'):
            logger.debug("sim monitor: waiting on pid: %s" % self.simulation.pid)
            self.simulation.message = self.last_status_line()
            self.update_status()
            time.sleep(self.MONITOR_SLEEP)
        logger.debug("sim_monitor: done waiting on pid: %s" % self.simulation.pid)
        sim_pid = self.simulation.pid #seems silly, but debug output below shows None if we don't do this

        # When poll returns None, the process is done, test if succeeded or failed
        last_message = self.last_status_line()
        last_state = self.check_state()
        if "Done" in last_message:
            self.simulation.status = SimulationState.Succeeded.value
            # Wise to wait a little bit to make sure files are written
            self.success(self.simulation)
        else:
            # If we exited with a Canceled status, don't update to Failed
            if not last_state == SimulationState.Canceled.value:
                self.simulation.status = SimulationState.Failed.value

        # Set the final simulation state
        logger.debug("sim_monitor: Updating sim: %s with pid: %s to status: %s" %
                     (self.simulation.id, sim_pid, self.simulation.status))
        self.simulation.message = last_message
        self.simulation.pid = None
        self.update_status()


    def update_status(self):
        self.states.put({'sid':self.simulation.id,
                         'status':self.simulation.status,
                         'message':self.simulation.message,
                         'pid':self.simulation.pid})

    def last_status_line(self):
        """
        Returns the last line of the status.txt file for the simulation.
        None if the file doesnt exist or is empty
        :return:
        """
        status_path = os.path.join(self.sim_dir, 'status.txt')
        msg = None
        if os.path.exists(status_path) and os.stat(status_path).st_size != 0:
            with open(status_path, 'r') as status_file:
                msg = list(status_file)[-1]

        return msg.strip('\n') if msg else ""

    def check_state(self):
        """
        Update the simulation and check its state
        Returns: state of the simulation or None
        """
        self.simulation = DataStore.get_simulation(self.simulation.id)
        return self.simulation.status

