import os
import shlex
import subprocess
import time

import psutil
from simtools.DataAccess.DataStore import DataStore


class LocalSimulationCommissioner:
    """
    Run one simulation.
    """
    def __init__(self, simulation, experiment, thread_queue, states,  success):
        self.experiment = experiment
        self.queue = thread_queue
        self.simulation = simulation
        self.sim_dir = self.simulation.get_path()
        self.states = states
        self.success = success

        if self.simulation.status == "Waiting":
            self.run()
        else:
            self.queue.get()
            if self.simulation.status in ('Failed', 'Succeeded', 'Cancelled'):
                return

            self.monitor()

    def run(self):
        try:
            with open(os.path.join(self.sim_dir, "StdOut.txt"), "w") as out:
                with open(os.path.join(self.sim_dir, "StdErr.txt"), "w") as err:
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
                    self.simulation.status = "Running"
                    self.update_status()

            self.monitor()
        except Exception as e:
            print "Error encountered while running the simulation."
            print e
        finally:
            # Free up an item in the queue
            self.queue.get()

    def monitor(self):
        # Wait the end of the process
        # We use poll to be able to update the status
        if self.simulation.pid:
            pid = int(self.simulation.pid)
            while psutil.pid_exists(pid) and psutil.Process(pid).name() == 'Eradication.exe':
                self.simulation.message = self.last_status_line()
                self.update_status()

                time.sleep(4)

        # When poll returns None, the process is done, test if succeeded or failed
        last_message = self.last_status_line()
        if "Done" in last_message:
            self.simulation.status = "Succeeded"
            # Wise to wait a little bit to make sure files are written
            self.success(self.simulation)
        else:
            last_state = self.check_state()
            # If we exited with a Canceled status, dont update to Failed
            if not last_state == 'Canceled':
                self.simulation.status = "Failed"

        # Set the final simulation state
        self.simulation.message = last_message
        self.simulation.pid = None
        self.update_status()

    def update_status(self):
        self.states[self.simulation.id] = self.simulation

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

