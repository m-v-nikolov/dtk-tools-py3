import os
import random
import string

from simtools.SimulationCreator.BaseSimulationCreator import BaseSimulationCreator


class LocalSim:
    def __init__(self, sim_id, sim_dir):
        self.id = sim_id
        self.tags = {}
        self.name = ""
        self.sim_dir = sim_dir


class LocalSimulationCreator(BaseSimulationCreator):
    def create_simulation(self, cb, error=0):
        sim_id = "Simulation_{}".format(self.generate_UUID())
        sim_dir = os.path.join(self.experiment.get_path(), sim_id)

        try:
            os.makedirs(sim_dir)
        except OSError:
            if error < 5:
                return self.create_simulation(cb, error+1)
            else:
                raise RuntimeError('Cannot create simulation directory: %s' % sim_dir)

        return LocalSim(sim_dir=sim_dir, sim_id=sim_id)

    @staticmethod
    def generate_UUID():
        return ''.join(random.choice(string.digits+string.ascii_uppercase) for _ in range(5))

    def save_batch(self):
        pass

    def pre_creation(self):
        pass

    def add_files_to_simulation(self, s, cb):
       cb.dump_files(s.sim_dir)

    def set_tags_to_simulation(self,s, tags, cb):
        s.tags = tags