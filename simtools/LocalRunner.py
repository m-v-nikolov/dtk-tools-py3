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
        with open(os.path.join(self.sim_dir, "StdOut.txt"), "w") as out:
            with open(os.path.join(self.sim_dir, "StdErr.txt"), "w") as err:
                p = subprocess.Popen(self.eradication_command.split(),
                                     cwd=self.sim_dir, shell=False, stdout=out, stderr=err)

                job_id = p.pid

                # We are now running
                self.change_state(job_id, status="Running")

                # Wait the end of the process
                # We use poll to be able to update the status
                while p.poll() is None:
                    time.sleep(1)
                    self.change_state(job_id, message=self.last_status_line())

                # When poll returns None, the process is done, test if succeeded or failed
                if "Done" in self.last_status_line():
                    self.change_state(job_id, status="Finished")
                else:
                    self.change_state(job_id, status="Failed")

                # Free up an item in the queue
                self.queue.get()

    def last_status_line(self):
        status_path = os.path.join(self.sim_dir, 'status.txt')
        msg = None
        if os.path.exists(status_path) and os.stat(status_path).st_size != 0:
            with open(status_path, 'r') as status_file:
                msg = list(status_file)[-1]

        return msg

    def change_state(self, job_id, status=None, message=None):
        self.lock.acquire()
        cache = json.load(open(self.cache_path, 'rb'))
        cache['sims'][self.sim_id]["jobId"] = job_id
        if status:
            cache['sims'][self.sim_id]["status"] = status
        if message:
            cache['sims'][self.sim_id]["message"] = message

        cache_file = open(self.cache_path, 'wb')
        json.dump(cache, cache_file, indent=4)
        cache_file.close()
        self.lock.release()

if __name__ == "__main__":
    import sys

    # Retrieve the info from the command line
    paths = sys.argv[1].split(',')
    command = sys.argv[2]
    queue_size = int(sys.argv[3])
    cache_path = sys.argv[4]

    queue = Queue(maxsize=queue_size)
    lock = threading.RLock()

    # Go through the paths and commission
    for path in paths:
        queue.put('run1')
        t = SimulationCommissioner(path, command, queue, cache_path, lock)
        t.start()
