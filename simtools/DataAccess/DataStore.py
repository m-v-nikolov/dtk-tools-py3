import json
import logging

from sqlalchemy.orm import joinedload

from simtools.DataAccess import engine, session_scope
from simtools.DataAccess.Schema import Base, Experiment, Simulation

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def dumper(obj):
    try:
        return obj.toJSON()
    except:
        if isinstance(obj, set):
            return list(obj)
        return obj.__dict__


class DataStore:
    def __init__(self):
        Base.metadata.create_all(engine)

    @classmethod
    def create_simulation(cls, **kwargs):
        return Simulation(**kwargs)

    @classmethod
    def create_experiment(cls, **kwargs):
        return Experiment(**kwargs)

    @classmethod
    def get_experiment(cls, exp_id):
        with session_scope() as session:
            # Get the experiment
            # Also load the associated simulations eagerly
            experiment = session.query(Experiment).options(joinedload('simulations'))\
                                                  .filter(Experiment.exp_id == exp_id).one()
            # Detach the object from the session
            session.expunge_all()

        return experiment

    @classmethod
    def save_simulation(cls,simulation):
        with session_scope() as session:
            session.merge(simulation)

    @classmethod
    def save_experiment(cls, experiment, verbose=True):
        if verbose:
            logger.info('Saving meta-data for experiment:')
            logger.info(json.dumps(experiment, indent=3, default=dumper, sort_keys=True))

        with session_scope() as session:
            session.merge(experiment)

    @classmethod
    def get_simulation(cls,sim_id):
        with session_scope() as session:
            simulation = session.query(Simulation).filter(Simulation.id==sim_id).one()
            session.expunge_all()

        return simulation
