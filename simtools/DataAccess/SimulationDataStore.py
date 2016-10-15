import datetime

from simtools.DataAccess import session_scope
from simtools.DataAccess.Schema import Simulation
from sqlalchemy import bindparam
from sqlalchemy import update

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
        if len(simulation_batch) == 0: return

        with session_scope() as session:
            stmt = update(Simulation).where(Simulation.id == bindparam("sid")).values(status=bindparam("status"), message=bindparam("message"), pid=bindparam("pid"))
            session.execute(stmt, simulation_batch)

    @classmethod
    def get_simulation_states(cls, simids):
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
        return Simulation(date_created=datetime.datetime.now(), **kwargs)

    @classmethod
    def save_simulation(cls, simulation):
        with session_scope() as session:
            session.merge(simulation)

    @classmethod
    def get_simulation(cls, sim_id):
        with session_scope() as session:
            simulation = session.query(Simulation).filter(Simulation.id == sim_id).one()
            session.expunge_all()

        return simulation
