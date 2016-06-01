import json
import os
import subprocess
import threading

from multiprocessing import Queue


class SimulationCommissioner(threading.Thread):
    def __init__(self, sim_dir, eradication_command, thread_queue, cache_file_path):
        threading.Thread.__init__(self)
        self.sim_dir = sim_dir
        self.eradication_command = eradication_command
        self.queue = thread_queue
        self.cache_path = cache_file_path

    def run(self):
        with open(os.path.join(self.sim_dir, "StdOut.txt"), "w") as out:
            with open(os.path.join(self.sim_dir, "StdErr.txt"), "w") as err:
                p = subprocess.Popen(self.eradication_command.split(),
                                     cwd=self.sim_dir, shell=False, stdout=out, stderr=err)

                # Write the pid in the cache file
                cache = json.load(open(self.cache_path, 'rb'))
                sim_id = self.sim_dir.split(os.sep)[-1]
                cache['sims'][sim_id]["jobId"] = p.pid

                with open(self.cache_path, 'wb') as cache_file:
                    json.dump(cache, cache_file, indent=4)

                # Wait the end of the run
                p.wait()
                self.queue.get()


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
        t = SimulationCommissioner(path, command, queue, cache_path)
        t.start()
