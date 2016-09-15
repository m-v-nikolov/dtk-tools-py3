import os
import pickle
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
    def __init__(self, simulation, experiment,analyzers, thread_queue, max_threads):
        threading.Thread.__init__(self)
        self.simulation = simulation
        self.experiment = experiment
        self.analyzers = analyzers
        self.data = {}
        self.queue = thread_queue
        self.max_threads = max_threads
        self.sim_dir = self.simulation.get_path()

    def run(self):
        try:
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
                        self.update_status(self.simulation, message=self.last_status_line(), pid=p.pid, status="Running")
                        time.sleep(1)

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
        for state in states:
            if state['sid'] == simulation.id and state['status'] != "Succeeded":
                state['status'] = status
                state['message'] = message
                state['pid'] = pid
                return

        states.append({
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
        parsers[parser.sim_id] = parser


def SimulationStateUpdater(loop=True):
    while True:
        DataStore.batch_simulations_update(states)
        states[:] = []
        if not loop: return
        time.sleep(3)


if __name__ == "__main__":
    import sys

    # Retrieve the info from the command line
    queue_size = int(sys.argv[1])
    exp_id = sys.argv[3]
    max_analysis_threads = int(sys.argv[2])

    # Create the queue
    queue = Queue(maxsize=queue_size)

    # Store the parsers and the states globally
    parsers = {}
    states = []

    # Start our SimulationStateUpdate thread (in charge of batch updating the simulations in the DB)
    t1 = threading.Thread(target=SimulationStateUpdater, args=(True,))
    t1.daemon = True
    t1.start()

    # max thread semaphone
    max_threads = threading.Semaphore(max_analysis_threads)

    # Retrieve the experiment
    current_exp = DataStore.get_experiment(exp_id)
    analyzers = [pickle.loads(analyzer.analyzer) for analyzer in current_exp.analyzers]

    # Go through the paths and commission
    threads = []
    for sim in current_exp.simulations:
        queue.put('run1')
        t = SimulationCommissioner(sim, current_exp, analyzers, queue, max_threads)
        threads.append(t)
        t.start()

    # Make sure we are all done
    map(lambda t: t.join(), threads)

    # Write the status a last time
    SimulationStateUpdater(False)

    if len(analyzers) != 0:
        # We are all done, finish analyzing
        for p in parsers.values():
            p.join()

        for a in analyzers:
            a.combine(parsers)
            a.finalize()
