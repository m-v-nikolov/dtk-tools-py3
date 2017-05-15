import datetime

from simtools.DataAccess import session_scope
from simtools.DataAccess.Schema import Simulation
from sqlalchemy import and_
from sqlalchemy import bindparam
from sqlalchemy import not_
from sqlalchemy import update

from simtools.Utilities.General import init_logging
logger = init_logging('DataAccess')
from COMPS.Data.Simulation import SimulationState

class SimulationDataStore:

    @classmethod
    def batch_simulations_update(cls, simulation_batch):
        """
        Takes a batch of simulations and update their status in the DB.
        This function provides performance considerations when updating large number of simulations in the db.

        The batch needs to be formatted as follow:
        [
            {'sid':'simid', "status": 'simstatus', "message":'message', "pid":123},
            {'sid':'simid', "status": 'simstatus', "message":'message', "pid":123}
        ]

        Args:
            batch: Batch of simulations to save
        """
        logger.debug("Batch simulations update")
        if len(simulation_batch) == 0: return

        for h in simulation_batch:
            h["status"] = h["status"].name # SimulationState -> name

        with session_scope() as session:
            stmt = update(Simulation).where(and_(Simulation.id == bindparam("sid"),
                                                 not_(Simulation.status in (SimulationState.Succeeded, SimulationState.Failed, SimulationState.Canceled))))\
                .values(status_s=bindparam("status"), message=bindparam("message"), pid=bindparam("pid"))
            session.execute(stmt, simulation_batch)

    @classmethod
    def bulk_insert_simulations(cls,simulations):
        with session_scope() as session:
            session.bulk_save_objects(simulations)

    @classmethod
    def get_simulation_states(cls, simids):
        logger.debug("Get simulation states")
        states_ret = []
        from simtools.DataAccess.DataStore import batch
        for ids in batch(simids, 50):
            with session_scope() as session:
                states = session.query(Simulation.id, Simulation.status).filter(Simulation.id.in_(ids)).all()
                session.expunge_all()
            states_ret.extend(states)
        return states_ret

    @classmethod
    def create_simulation(cls, **kwargs):
        logger.debug("Create simulation")
        if 'date_created' not in kwargs:
            kwargs['date_created'] = datetime.datetime.now()
        return Simulation(**kwargs)

    @classmethod
    def save_simulation(cls, simulation, session=None):
        logger.debug("Save simulation")
        with session_scope(session) as session:
            session.merge(simulation)

    @classmethod
    def get_simulation(cls, sim_id):
        logger.debug("Get simulation")
        with session_scope() as session:
            simulation = session.query(Simulation).filter(Simulation.id == sim_id).one_or_none()
            session.expunge_all()

        return simulation

    @classmethod
    def delete_simulation(cls, simulation):
        logger.debug("Delete simulation %s" % simulation.id)
        with session_scope() as session:
            session.delete(session.query(Simulation).filter(Simulation.id == simulation.id).one())
