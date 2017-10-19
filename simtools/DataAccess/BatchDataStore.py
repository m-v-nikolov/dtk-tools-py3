from sqlalchemy import all_
from sqlalchemy.orm import joinedload

from simtools.DataAccess import session_scope
from simtools.DataAccess.Schema import Batch, BatchSimulation, BatchExperiment
from operator import and_, or_


class BatchDataStore:
    @classmethod
    def get_batch_by_id(cls, batch_id):
        if batch_id is None:
            return None

        with session_scope() as session:
            batch = session.query(Batch).filter(Batch.id == batch_id).one_or_none()
            session.expunge_all()

        return batch

    @classmethod
    def get_batch_by_name(cls, batch_name):
        with session_scope() as session:
            batch = session.query(Batch).filter(Batch.name == batch_name) \
                .options(joinedload('simulations').joinedload('experiment')) \
                .one_or_none()
            session.expunge_all()

        return batch

    @classmethod
    def save_batch(cls, batch):
        with session_scope() as session:
            if not batch.id:
                session.add(batch)
                session.flush()
                if not batch.name:
                    batch.name = 'batch_%s' % batch.id

                session.merge(batch)
                session.expunge_all()
            else:
                session.merge(batch)

    @classmethod
    def get_batch_list(cls, id_or_name=None):
        batches = None
        with session_scope() as session:
            try:
                batch_id = int(id_or_name)
                batches = session.query(Batch).filter(Batch.id == batch_id) \
                    .options(joinedload('simulations').joinedload('experiment')).all()
            except: pass

            if not batches:
                batches = session.query(Batch) \
                    .filter(Batch.name.like("%{}%".format(id_or_name or ""))) \
                    .options(joinedload('simulations').joinedload('experiment')).all()

            session.expunge_all()

        return batches

    @classmethod
    def delete_batch(cls, batch_id=None):
        with session_scope() as session:
            if batch_id:
                batches = session.query(Batch).filter(Batch.id == batch_id).one_or_none()
                if batches:
                    session.delete(batches)
            else:
                batches = session.query(Batch).all()
                for batch in batches:
                    session.delete(batch)

    @classmethod
    def remove_empty_batch(cls):
        cnt = 0
        with session_scope() as session:
            batches = session.query(Batch).filter(and_(~Batch.experiments.any(), ~Batch.simulations.any())).all()

            for batch in batches:
                session.delete(batch)
                cnt += 1

        return cnt

    @classmethod
    def clear_batch(cls, batch=None):
        if batch is None:
            return

        with session_scope() as session:
            batch = session.query(Batch).filter(Batch.id == batch.id).one_or_none()
            if batch:
                batch.experiments = []
                batch.simulations = []
                session.merge(batch)
