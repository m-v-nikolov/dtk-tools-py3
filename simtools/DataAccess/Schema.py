import datetime
import json

from sqlalchemy import Column
from sqlalchemy import Date
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import PickleType
from sqlalchemy import String
from sqlalchemy.orm import relationship

from simtools.DataAccess import Base


class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True)
    status = Column(Enum('Waiting', 'Commissioned', 'Running', 'Succeeded', 'Failed',  'Cancelled'))
    message = Column(String)
    experiment = relationship("Experiment", back_populates="simulations")
    experiment_id = Column(String, ForeignKey('experiments.exp_id'))
    tags = Column(PickleType(pickler=json))

    def __repr__(self):
        return "Simulation %s (%s - %s)" % (self.id, self.status, self.message)

    def toJSON(self):
        return {'id': self.id, 'tags': self.tags}

class Experiment(Base):
    __tablename__ = "experiments"

    exp_id = Column(String, primary_key=True)
    dtk_tools_revision = Column(String)
    exe_name = Column(String)
    exp_name = Column(String)
    location = Column(String)
    selected_block = Column(String)
    setup_overlay_file = Column(String)
    sim_root = Column(String)
    sim_type = Column(String)
    command_line = Column(String)
    date_created = Column(Date, default=datetime.datetime.now())

    simulations = relationship("Simulation", back_populates='experiment')

    def __repr__(self):
        return "Experiment %s" % (self.id)