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
    def __init__(self, simulation, experiment, analyzers, thread_queue, max_threads, states, parsers):
        self.simulation = simulation
        self.experiment = experiment
        self.analyzers = analyzers
        self.queue = thread_queue
        self.max_threads = max_threads
        self.sim_dir = self.simulation.get_path()
        self.states = states
        self.parsers = parsers

        self.run()

    def run(self):
        try:
            # If we are just waiting -> run
            if self.check_state() == "Waiting":
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

            if self.check_state() == "Running":
                # Wait the end of the process
                # We use poll to be able to update the status
                pid = int(self.simulation.pid)
                while self.simulation.pid and psutil.pid_exists(pid) and psutil.Process(pid).name() == 'Eradication.exe':
                    self.update_status(self.simulation, message=self.last_status_line(), pid=pid, status="Running")
                    time.sleep(3)

                # When poll returns None, the process is done, test if succeeded or failed
                last_message = self.last_status_line()
                if "Done" in self.last_status_line():
                    self.update_status(self.simulation, status="Succeeded",  pid=-1, message=last_message)
                    # Wise to wait a little bit to make sure files are written
                    self.analyze_simulation()
                else:
                    # If we exited with a Canceled status, dont update to Failed
                    if not self.check_state() == 'Canceled':
                        self.update_status(self.simulation, status="Failed", pid=-1, message=last_message)
        except Exception as e:
            print "Error encountered while running the simulation."
            print e
        finally:
            # Free up an item in the queue
            self.queue.get()

    def update_status(self, simulation, status=None, message=None, pid=None):
        pid = pid if pid > 0 else None
        for state in self.states:
            if state['sid'] == simulation.id and state['status'] != "Succeeded":
                state['status'] = status
                state['message'] = message
                state['pid'] = pid
                return

        self.states.append({
            'sid':simulation.id,
            'status':status,
            'message':message,
            'pid': pid
        })

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

    def analyze_simulation(self):
        # Called when a simulation finishes
        filtered_analyses = [a for a in self.analyzers if a.filter(self.simulation.tags)]
        if not filtered_analyses:
            # logger.debug('Simulation did not pass filter on any analyzer.')
            return
        self.max_threads.acquire()
        from simtools.OutputParser import SimulationOutputParser
        parser = SimulationOutputParser(self.experiment.get_path(),
                                self.simulation.id,
                                self.simulation.tags,
                                filtered_analyses,
                                self.max_threads)
        parser.start()
        self.parsers[parser.sim_id] = parser

