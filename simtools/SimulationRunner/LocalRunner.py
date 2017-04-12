import os
import shlex
import subprocess
import time

import psutil
from simtools.DataAccess.DataStore import DataStore
from simtools.SimulationRunner.BaseSimulationRunner import BaseSimulationRunner

from simtools.Utilities.General import init_logging
logger = init_logging("LocalRunner")


class LocalSimulationRunner(BaseSimulationRunner):
    """
    Run one simulation.
    """
    def __init__(self, simulation, experiment, states, success):
        super(LocalSimulationRunner, self).__init__(experiment, states, success)
        self.simulation = simulation
        self.sim_dir = self.simulation.get_path()

        if self.check_state() == "Waiting":
            self.run()
        elif self.simulation.status not in ('Failed', 'Succeeded', 'Cancelled'):
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
                self.simulation.status = "Running"
                self.update_status()

            self.monitor()
        except Exception as e:
            print "Error encountered while running the simulation."
            print e

    def monitor(self):
        # Wait the end of the process
        # We use poll to be able to update the status
        while self.is_running(self.simulation.pid): #psutil.pid_exists(pid) and "Eradication" in psutil.Process(pid).name():
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
            self.simulation.status = "Succeeded"
            # Wise to wait a little bit to make sure files are written
            self.success(self.simulation)
        else:
            # If we exited with a Canceled status, don't update to Failed
            if not last_state == 'Canceled':
                self.simulation.status = "Failed"

        # Set the final simulation state
        logger.debug("sim_monitor: Updating sim: %s with pid: %s to status: %s" %
                     (self.simulation.id, sim_pid, self.simulation.status))
        self.simulation.message = last_message
        self.simulation.pid = None
        self.update_status()

    @classmethod
    def is_running(cls, pid):
        '''
        Determines if the given pid is running and is running Eradication.exe
        :return: True/False
        '''
        # ck4, BaseExperimentManager uses virtually identical logic. Should combine the codes.
        # ck4, This should be refactored to use a common module containing a dict of Process objects
        #      This way, we don't need to do the name() checking, just use the method process.is_running(),
        #      since this method checks for pid number being active AND pid start time.
        if pid:
            pid = int(pid)
            try:
                process = psutil.Process(pid)
            except psutil.NoSuchProcess:
                logger.debug("is_running: No such process pid: %d" % pid)
                is_running = False
                process_name = None
                valid_name = False
            else:
                is_running = True
                process_name = process.name()
                valid_name = "Eradication" in process_name

            logger.debug("is_running: pid %s running? %s valid_name? %s. name: %s" % (pid, is_running, valid_name, process_name))
            if is_running and valid_name:
                logger.debug("is_running: pid %s is running and process name is valid." % pid)
                return True
            else:
                return False
        else:
            logger.debug("is_running: no valid pid provided.")
            return False

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

