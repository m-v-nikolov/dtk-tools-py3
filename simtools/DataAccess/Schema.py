import datetime
import inspect
import os
from sqlalchemy import Binary
from sqlalchemy import Column
from sqlalchemy import DateTime
from sqlalchemy import Enum
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import PickleType
from sqlalchemy import String
from sqlalchemy.ext.hybrid import hybrid_property
from sqlalchemy.orm import relationship

from simtools.DataAccess import Base, engine
from COMPS.Data.Simulation import SimulationState

class Analyzer(Base):
    __tablename__ = "analyzers"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String)
    analyzer = Column(Binary)
    experiment_id = Column(String, ForeignKey('experiments.exp_id'))
    experiment = relationship("Experiment", back_populates="analyzers")

class Settings(Base):
    __tablename__ = "settings"
    key = Column(String, primary_key=True)
    value = Column(String)

class Simulation(Base):
    __tablename__ = "simulations"

    id = Column(String, primary_key=True)
    status_s = Column(String, default=SimulationState.Created.name)
    message = Column(String)
    experiment = relationship("Experiment", back_populates="simulations")
    experiment_id = Column(String, ForeignKey('experiments.exp_id'))
    tags = Column(PickleType())
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.now())
    pid = Column(String)

    # A pair of accessors to support SumulationState-only status comparison external to DB access.
    @property
    def status(self):
        """
        Allows us to compare status values uniformly in the code with SimulationState objects.
        :return: SimulationState object corresponding to the DB int status
        """
        return SimulationState[self.status_s]

    @status.setter
    def status(self, st):
        if isinstance(st, SimulationState):
            self.status_s = st.name
        else:
            raise Exception("Invalid status type: %s" % type(st))

    def __repr__(self):
        return "Simulation %s (%s - %s)" % (self.id, self.status.name, self.message)

    def toJSON(self):
        return {self.id: self.tags}

    def get_path(self, save_map=True):
        if self.experiment.location == "LOCAL":
            return os.path.join(self.experiment.sim_root, '%s_%s' % (self.experiment.exp_name, self.experiment.exp_id), self.id)
        else:
            from simtools.OutputParser import CompsDTKOutputParser
            if not CompsDTKOutputParser.sim_dir_map or self.id not in CompsDTKOutputParser.sim_dir_map:
                map = CompsDTKOutputParser.createSimDirectoryMap(exp_id=self.experiment.exp_id, save=save_map)
                return map[self.id]

            return CompsDTKOutputParser.sim_dir_map[self.id]

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
    working_directory = Column(String)
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.now())
    endpoint = Column(String)

    simulations = relationship("Simulation", back_populates='experiment', cascade="all, delete-orphan", order_by="Simulation.date_created")
    analyzers = relationship("Analyzer", back_populates='experiment', cascade="all, delete-orphan")

    def __repr__(self):
        format_string = "{date} - {name} : {id} ({location}) - {sim_count} simulations - {state}"
        return format_string.format(date=self.date_created.strftime('%m/%d/%Y %H:%M:%S'),
                                       name=self.exp_name, id=self.exp_id, location=self.location,
                                       sim_count=len(self.simulations),
                                       state="Completed" if self.is_done() else "Not Completed")

    @hybrid_property
    def id(self):
        return "%s_%s" % (self.exp_name,self.exp_id)

    def get_path(self):
        if self.location == "LOCAL":
            return os.path.join(self.sim_root, self.id)

    def contains_simulation(self, simid):
        for sim in self.simulations:
            if sim.id == simid:
                return True
        return False

    def get_simulations_with_tag(self, tag, value):
        return [sim for sim in self.simulations if sim.tags.has_key(tag) and sim.tags[tag] == value]

    def get_simulation_by_id(self, sim_id):
        for sim in self.simulations:
            if sim.id == sim_id:
                return sim

    def is_done(self):
        for sim in self.simulations:
            if sim.status not in (SimulationState.Succeeded, SimulationState.Failed, SimulationState.Canceled):
                return False
        return True

    def is_successful(self):
        for sim in self.simulations:
            if sim.status != SimulationState.Succeeded:
                return False
        return True

    def toJSON(self):
        ret = {}
        for name in dir(self):
            # For now skip the analyzers
            if name == "analyzers": continue

            value = getattr(self, name)

            # Weed out the internal parameters/methods
            if name.startswith('_') or name in ('metadata') or inspect.ismethod(value):
                continue

            # Special case for the simulations
            if name == 'simulations':
                ret['simulations'] = {}
                for sim in value:
                    ret['simulations'][sim.id] = sim.tags
                continue

            if name == 'analyzers':
                ret['analyzers'] = []
                for a in value:
                    ret['analyzers'].append(a.name)
                continue

            # By default just add to the dict
            ret[name] = value

        return ret


class Batch(Base):
    __tablename__ = "batches"
    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, unique=True, nullable=True)
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.now())

    experiments = relationship("Experiment", secondary="batch_experiment", lazy='subquery',
                               order_by="Experiment.date_created")

    simulations = relationship("Simulation", secondary="batch_simulation", lazy='subquery',
                               order_by="Simulation.date_created")

    def __repr__(self):
        return "%s (id=%s)" % (self.name, self.id)

    # must be called from an instance
    def get_experiment_ids(self):
        exp_ids = [exp.exp_id for exp in self.experiments]
        return exp_ids

    # must be called from an instance
    def get_simulation_ids(self):
        sim_ids = [sim.id for sim in self.simulations]
        return sim_ids


class BatchExperiment(Base):
    __tablename__ = "batch_experiment"
    batch_id = Column(String, ForeignKey('batches.id'), primary_key=True)
    exp_id = Column(String, ForeignKey('experiments.exp_id'), primary_key=True)
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.now())

    def __repr__(self):
        return "batch_experiment"


class BatchSimulation(Base):
    __tablename__ = "batch_simulation"
    batch_id = Column(String, ForeignKey('batches.id'), primary_key=True)
    sim_id = Column(String, ForeignKey('simulations.id'), primary_key=True)
    date_created = Column(DateTime(timezone=True), default=datetime.datetime.now())

    def __repr__(self):
        return "batch_simulation"

Base.metadata.create_all(engine)