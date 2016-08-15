import os
import shlex
import subprocess
import threading
import time
from multiprocessing import Queue

from simtools.DataAccess.DataStore import DataStore


class SimulationCommissioner(threading.Thread):
    """
    Run one simulation.
    """
    def __init__(self, simulation, experiment, thread_queue):
        threading.Thread.__init__(self)
        self.simulation = simulation
        self.experiment = experiment
        self.queue = thread_queue

        self.sim_dir = self.simulation.get_path(self.experiment)

    def run(self):
        # Make sure the status is not set.
        # If it is, dont touch this simulation
        if self.check_state() != "Waiting":
            self.queue.get()
            return

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
                DataStore.change_simulation_state(self.simulation, status="Running", pid=p.pid)

                # Wait the end of the process
                # We use poll to be able to update the status
                while p.poll() is None:
                    DataStore.change_simulation_state(self.simulation, message=self.last_status_line())
                    time.sleep(3)

                # When poll returns None, the process is done, test if succeeded or failed
                last_message = self.last_status_line()
                if "Done" in self.last_status_line():
                    DataStore.change_simulation_state(self.simulation, status="Succeeded",  pid=-1, message=last_message)
                else:
                    # If we exited with a Canceled status, dont update to Failed
                    if not self.check_state() == 'Canceled':
                        DataStore.change_simulation_state(self.simulation, status="Failed", pid=-1, message=last_message)

                # Free up an item in the queue
                self.queue.get()

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


if __name__ == "__main__":
    import sys

    # Retrieve the info from the command line
    queue_size = int(sys.argv[1])
    exp_id = sys.argv[2]

    # Create the queue
    queue = Queue(maxsize=queue_size)

    # Retrieve the experiment
    current_exp = DataStore.get_experiment(exp_id)

    # Go through the paths and commission
    for sim in current_exp.simulations:
        queue.put('run1')
        t = SimulationCommissioner(sim, current_exp, queue)
        t.start()
