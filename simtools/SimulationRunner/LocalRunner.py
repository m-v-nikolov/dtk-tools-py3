import json
import os
import subprocess
import threading

from multiprocessing import Queue

import time


class SimulationCommissioner(threading.Thread):
    """
    Run one simulation.
    """
    def __init__(self, sim_dir, eradication_command, thread_queue, cache_path, lock):
        threading.Thread.__init__(self)
        self.sim_dir = sim_dir
        self.sim_id = self.sim_dir.split(os.sep)[-1]
        self.eradication_command = eradication_command
        self.queue = thread_queue
        self.cache_path = cache_path
        self.lock = lock

    def run(self):
        # Make sure the status is not set.
        # If it is, dont touch this simulation
        if self.check_state():
            self.queue.get()
            return

        with open(os.path.join(self.sim_dir, "StdOut.txt"), "w") as out:
            with open(os.path.join(self.sim_dir, "StdErr.txt"), "w") as err:
                p = subprocess.Popen(self.eradication_command.split(),
                                     cwd=self.sim_dir, shell=False, stdout=out, stderr=err)

                # We are now running
                self.change_state(status="Running", pid = p.pid)

                # Wait the end of the process
                # We use poll to be able to update the status
                while p.poll() is None:
                    time.sleep(1)
                    self.change_state(message=self.last_status_line())

                # Remove "pid" from cached json file.
                self.change_state(pid = -1)

                # When poll returns None, the process is done, test if succeeded or failed
                if "Done" in self.last_status_line():
                    self.change_state(status="Finished")
                else:
                    self.change_state(status="Failed")

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

        return msg if msg else ""

    def check_state(self):
        """
        Returns the state of the simulation.
        Returns: state of the simulation or None
        """
        # Acquire the lock
        self.lock.acquire()

        # Opeen the cache file
        json_file = open(self.cache_path,'rb')
        cache = json.load(json_file)

        # Get the status
        try:
            status = cache['sims'][self.sim_id]['status']
        except KeyError:
            status = None

        # Close the file and release the lock
        json_file.close()
        self.lock.release()

        return status

    def change_state(self, status=None, message=None, pid = None):
        """
        Change either status, message or both for the simulation currently handled by the thread.
        Everything inside the lock is in a try, finally block to prevent infinite blocking even if something goes wrong.
        :param status:
        :param message:
        :return:
        """
        # Acquire the lock on the file
        self.lock.acquire()
        try:
            # Open the metadata file
            json_file = open(self.cache_path, 'rb')
            cache = json.load(json_file)

            # If we have a status, set it (same for message)
            if status:
                cache['sims'][self.sim_id]["status"] = status
            if message:
                cache['sims'][self.sim_id]["message"] = message
            if pid:
                if pid == -1 and 'pid' in cache['sims'][self.sim_id]:
                    del cache['sims'][self.sim_id]["pid"]
                else:
                    cache['sims'][self.sim_id]["pid"] = pid

            # Write the file back
            with open(self.cache_path, 'wb') as cache_file:
                json.dump(cache, cache_file, indent=4)

        finally:
            # Close the file
            json_file.close()

            # To finish release the lock
            self.lock.release()

if __name__ == "__main__":
    import sys

    # Retrieve the info from the command line
    paths = sys.argv[1].split(',')
    command = sys.argv[2]
    queue_size = int(sys.argv[3])
    cache_path = sys.argv[4]

    # Create the queue and the re-entrant lock
    queue = Queue(maxsize=queue_size)
    lock = threading.RLock()

    # Go through the paths and commission
    for path in paths:
        queue.put('run1')
        t = SimulationCommissioner(path, command, queue, cache_path, lock)
        t.start()
