from simtools.DataAccess import session_scope
from simtools.DataAccess.Schema import Batch, BatchExperiment
from simtools.DataAccess.Schema import Experiment, Simulation
from sqlalchemy import func
from operator import or_, is_


class BatchDataStore:

    @classmethod
    def get_batch(cls, batch):
        if batch is None:
            return None

        with session_scope() as session:
            batch = session.query(Batch).filter(Batch.id == batch.id).one_or_none()
            session.expunge_all()

        return batch

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
        if batch_name is None:
            return None

        with session_scope() as session:
            batch = session.query(Batch).filter(Batch.name == batch_name).one_or_none()
            session.expunge_all()

        return batch

    @classmethod
    def save_batch(cls, batch):
        existing = True if BatchDataStore.get_batch_by_name(batch.name) else False

        batch_before = BatchDataStore.get_batch_list()
        with session_scope() as session:
            session.merge(batch)

        batch_after = BatchDataStore.get_batch_list()

        if existing:
            return batch.id
        else:
            batch_before = [b.id for b in batch_before]
            batch_after = [b.id for b in batch_after]

            batch_diff = set(batch_after) - set(batch_before)

            if len(batch_diff) == 1:
                return list(batch_diff)[0]
            else:
                return None

    @classmethod
    def get_batch_list(cls, batch_id=None):
        with session_scope() as session:
            if batch_id:
                batches = session.query(Batch).filter(Batch.id == batch_id).one_or_none()
            else:
                batches = session.query(Batch).all()

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
            batches = session.query(Batch).filter(~Batch.experiments.any()).all()

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
                session.merge(batch)

    @classmethod
    def get_expIds_by_batchIds(cls, batch_ids):
        """
        Get the experiments which are associated with batch_ids
        batch_ids: list of batch ids
        """
        if batch_ids is None or len(batch_ids) == 0:
            return []

        with session_scope() as session:
            exp_list = session.query(BatchExperiment).filter(BatchExperiment.batch_id.in_(batch_ids)).all()
            session.expunge_all()

        exp_ids = [exp.exp_id for exp in exp_list]

        return exp_ids