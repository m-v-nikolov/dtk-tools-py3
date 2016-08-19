import json
import logging

import datetime
from sqlalchemy import or_
from sqlalchemy.orm import joinedload

from simtools.DataAccess import session_scope
from simtools.DataAccess.Schema import Experiment, Simulation
from simtools.utils import remove_null_values

logging.basicConfig(format='%(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)


def dumper(obj):
    """
    Function to pass to the json.dump function.
    Allows to call the toJSON() function on the objects that needs to be serialized.
    Revert to the __dict__ if failure to invoke the toJSON().
    Args:
        obj: the object to serialize
    Returns:
        Serializable format
    """
    try:
        return obj.toJSON()
    except:
        if isinstance(obj, set):
            return list(obj)
        if isinstance(obj,datetime.datetime):
            return obj.isoformat()
        return obj.__dict__


class DataStore:
    """
    Class to abstract access to the data.
    """

    @classmethod
    def batch_simulations_update(cls, batch):
        with session_scope() as session:
            for simulation in batch:
                session.merge(simulation)

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
            experiment = session.query(Experiment).options(joinedload('simulations').joinedload('experiment'))\
                                                  .filter(Experiment.exp_id == exp_id).one()
            # Detach the object from the session
            session.expunge_all()

        return experiment

    @classmethod
    def save_simulation(cls, simulation):
        with session_scope() as session:
            session.merge(simulation)

    @classmethod
    def save_experiment(cls, experiment, verbose=True):
        if verbose:
            # Dont display the null values
            logger.info('Saving meta-data for experiment:')
            logger.info(json.dumps(remove_null_values(experiment.toJSON()), indent=3, default=dumper, sort_keys=True))

        with session_scope() as session:
            session.merge(experiment)

    @classmethod
    def get_simulation(cls, sim_id):
        with session_scope() as session:
            simulation = session.query(Simulation).filter(Simulation.id == sim_id).one()
            session.expunge_all()

        return simulation

    @classmethod
    def get_most_recent_experiment(cls, id_or_name):
        id_or_name = '' if not id_or_name else id_or_name
        with session_scope() as session:
            experiment = session.query(Experiment)\
                .filter(Experiment.id.like('%%%s%%' % id_or_name)) \
                .options(joinedload('simulations')) \
                .order_by(Experiment.date_created.desc()).first()

            session.expunge_all()
        return experiment

    @classmethod
    def get_active_experiments(cls):
        with session_scope() as session:
            experiments = session.query(Experiment).distinct(Experiment.exp_id)\
                .join(Experiment.simulations)\
                .filter(or_(Simulation.status.in_(("Running", "Waiting")), Simulation.status.is_(None)))
            session.expunge_all()

        return experiments

    @classmethod
    def get_experiments(cls, id_or_name, current_dir=None):
        id_or_name = '' if not id_or_name else id_or_name
        with session_scope() as session:
            experiments = session.query(Experiment).filter(Experiment.id.like('%%%s%%' % id_or_name))
            if current_dir:
                experiments = experiments.filter(Experiment.working_directory == current_dir)
            session.expunge_all()

        return experiments

    @classmethod
    def delete_experiment(cls, experiment):
        with session_scope() as session:
            session.delete(session.query(Experiment).filter(Experiment.id == experiment.id).one())

    @classmethod
    def change_simulation_state(cls, simulation, message=None, status=None, pid=None):
        with session_scope() as session:
            simulation = session.query(Simulation).filter(Simulation.id == simulation.id).one()
            if message:
                simulation.message = message

            if status:
                simulation.status = status

            if pid:
                simulation.pid = pid if pid > 0 else None