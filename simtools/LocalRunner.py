import json
import os
import subprocess
import threading

from multiprocessing import Queue

import time


class SimulationCommissioner(threading.Thread):
    def __init__(self, sim_dir, eradication_command, thread_queue):
        threading.Thread.__init__(self)
        self.sim_dir = sim_dir
        self.eradication_command = eradication_command
        self.queue = thread_queue
        self._job_id = None

    def run(self):
        with open(os.path.join(self.sim_dir, "StdOut.txt"), "w") as out:
            with open(os.path.join(self.sim_dir, "StdErr.txt"), "w") as err:
                p = subprocess.Popen(self.eradication_command.split(),
                                     cwd=self.sim_dir, shell=False, stdout=out, stderr=err)

                self._job_id = p.pid

                # Wait the end of the run
                p.wait()
                self.queue.get()

    @property
    def job_id(self):
        timeout = 10
        while (timeout > 0):
            if not self._job_id:
                time.sleep(0.1)
            return self._job_id

if __name__ == "__main__":
    import sys

    # Retrieve the info from the command line
    paths = sys.argv[1].split(',')
    command = sys.argv[2]
    queue_size = int(sys.argv[3])
    cache_path = sys.argv[4]

    queue = Queue(maxsize=queue_size)

    # Go through the paths and commission
    for path in paths:
        queue.put('run1')
        t = SimulationCommissioner(path, command, queue)
        t.start()

        # Write the pid in the cache file
        cache = json.load(open(cache_path, 'rb'))
        sim_id = path.split(os.sep)[-1]
        cache['sims'][sim_id]["jobId"] = t.job_id

        cache_file = open(cache_path, 'wb')
        json.dump(cache, cache_file, indent=4)
        cache_file.close()
