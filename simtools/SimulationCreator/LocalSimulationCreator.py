import multiprocessing
import os
import re
import time
from datetime import datetime
from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator


class LocalSim:
    def __init__(self, sim_id, sim_dir):
        self.id = sim_id
        self.tags = {}
        self.name = ""
        self.sim_dir = sim_dir


class LocalSimulationCreator(BaseSimulationCreator):
    creation_lock = multiprocessing.Lock()

    def create_simulation(self, cb):
        # Lock to avoid duplicated names
        self.creation_lock.acquire()
        time.sleep(0.01)
        sim_id = re.sub('[ :.-]', '_', str(datetime.now()))
        self.creation_lock.release()
        sim_dir = os.path.join(self.experiment.get_path(), sim_id)
        os.makedirs(sim_dir)
        return LocalSim(sim_dir=sim_dir, sim_id=sim_id)

    def post_creation(self):
        pass

    def pre_creation(self):
        pass

    def add_files_to_simulation(self, s, cb):
       cb.dump_files(s.sim_dir)

    def set_tags_to_simulation(self,s, tags):
        s.tags = tags