import multiprocessing
import os
import re
import time
from datetime import datetime
from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator


class LocalSim:
    def __init__(self, sim_id, sim_dir):
        self.id = sim_id
        self.tags = {'aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd','aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa':'dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd'}
        self.name = ""
        self.sim_dir = sim_dir


class LocalSimulationCreator(BaseSimulationCreator):

    def create_simulation(self, cb):
        sim_id = re.sub('[ :.-]', '_', str(datetime.now()))
        sim_dir = os.path.join(self.experiment.get_path(), sim_id)
        try:
            os.makedirs(sim_dir)
        except OSError:
            return self.create_simulation(cb)

        return LocalSim(sim_dir=sim_dir, sim_id=sim_id)

    def save_batch(self):
        pass

    def pre_creation(self):
        pass

    def add_files_to_simulation(self, s, cb):
       cb.dump_files(s.sim_dir)

    def set_tags_to_simulation(self,s, tags):
        s.tags = tags