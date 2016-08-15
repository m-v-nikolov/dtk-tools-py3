import datetime
import inspect
import json
import os

from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import PickleType
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from simtools.DataAccess import Base, engine


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True)
    status = Column(Enum('Waiting', 'Commissioned', 'Running', 'Succeeded', 'Failed',  'Canceled'))
    message = Column(String)
    experiment = relationship("Experiment", back_populates="simulations")
    experiment_id = Column(String, ForeignKey('experiments.exp_id'))
    tags = Column(PickleType(pickler=json))
    pid = Column(String)

    def __repr__(self):
        return "Simulation %s (%s - %s)" % (self.id, self.status, self.message)

    def toJSON(self):
        return {self.id: self.tags}

    def get_path(self,experiment):
        return os.path.join(experiment.sim_root, '%s_%s' % (experiment.exp_name, experiment.exp_id), self.id)


class Experiment(Base):
    __tablename__ = "experiments"

    exp_id = Column(String, primary_key=True)
    suite_id = Column(String)
    dtk_tools_revision = Column(String)
    exe_name = Column(String)
    exp_name = Column(String)
    location = Column(String)
    selected_block = Column(String)
    setup_overlay_file = Column(String)
    sim_root = Column(String)
    sim_type = Column(String)
    command_line = Column(String)
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.now())
    endpoint = Column(String)

    simulations = relationship("Simulation", back_populates='experiment', cascade="all, delete-orphan")

    def __repr__(self):
        return "Experiment %s" % self.id

    @hybrid_property
    def id(self):
        return self.exp_name + "_" + self.exp_id

    def get_path(self):
        return os.path.join(self.sim_root, self.id)

    def toJSON(self):
        ret = {}
        for name in dir(self):
            value = getattr(self, name)
            # Weed out the internal parameters/methods
            if name.startswith('_') or name in ('metadata','date_created') or inspect.ismethod(value):
                continue

            # Special case for the simulations
            if name == 'simulations':
                ret['simulations'] = {}
                for sim in value:
                    ret['simulations'][sim.id] = sim.tags
                continue

            # By default just add to the dict
            ret[name] = value

        return ret

Base.metadata.create_all(engine)