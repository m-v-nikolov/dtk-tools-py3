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
        return obj.__dict__


class DataStore:
    def __init__(self):
        Base.metadata.create_all(engine)

    def cache_experiment_data(self, experiment_data, verbose=True):
        if verbose:
            logger.info('Saving meta-data for experiment:')
            logger.info(json.dumps(experiment_data, indent=3, default=dumper, sort_keys=True))

        experiment = Experiment(**experiment_data)
        with session_scope() as session:
            session.merge(experiment)

    def create_simulation(self, id, tags):
        return Simulation(id=id, tags=tags)

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
    def get_simulation(cls,sim_id):
        with session_scope() as session:
            simulation = session.query(Simulation).filter(Simulation.id==sim_id).one()
            session.expunge_all()

        return simulation
