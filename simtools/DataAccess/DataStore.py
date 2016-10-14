import datetime
import json

from simtools.DataAccess import session_scope, logger
from simtools.DataAccess.Schema import Experiment, Simulation, Analyzer, Settings
from simtools.DataAccess.SimulationDataStore import SimulationDataStore
from simtools.utils import remove_null_values
from sqlalchemy.orm import joinedload


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
        if isinstance(obj, datetime.datetime):
            return str(obj)
        return obj.__dict__


def batch(iterable, n=1):
    """
    Batch an iterable passed as argument into lists of n elements.

    Examples:
        batch([1,2,3,4,5,6],2) returns [[1,2],[2,3],[4,5],[6]]

    Args:
        iterable: The iterable to split
        n: split in lists of n elements

    Returns: List of lists of n elements
    """
    logger.debug('batch function - %s in %s elements' % (iterable, n))

    l = len(iterable)
    for ndx in range(0, l, n):
        yield iterable[ndx:min(ndx + n, l)]


class DataStore(SimulationDataStore):
    """
    Class holding static methods to abstract the access to the database.
    """

    @classmethod
    def create_experiment(cls, **kwargs):
        return Experiment(**kwargs)

    @classmethod
    def create_analyzer(cls, **kwargs):
        return Analyzer(**kwargs)

    @classmethod
    def get_experiment(cls, exp_id):
        with session_scope() as session:
            # Get the experiment
            # Also load the associated simulations eagerly
            experiment = session.query(Experiment).options(joinedload('simulations').joinedload('experiment').joinedload('analyzers'))\
                                                  .filter(Experiment.exp_id == exp_id).one_or_none()

            # Detach the object from the session
            session.expunge_all()

        return experiment



    @classmethod
    def batch_save_experiments(cls, batch):
        with session_scope() as session:
            for exp in batch:
                DataStore.save_experiment(exp, False, session)

    @classmethod
    def save_experiment(cls, experiment, verbose=True, session=None):
        if verbose:
            # Dont display the null values
            logger.info('Saving meta-data for experiment:')
            logger.info(json.dumps(remove_null_values(experiment.toJSON()), indent=3, default=dumper, sort_keys=True))

        with session_scope(session) as session:
            session.merge(experiment)

    @classmethod
    def get_setting(cls,setting):
        with session_scope() as session:
            setting = session.query(Settings).filter(Settings.key == setting).one_or_none()
            session.expunge_all()

        return setting

    @classmethod
    def save_setting(cls, setting):
        with session_scope() as session:
            session.merge(setting)

    @classmethod
    def create_setting(cls, **kwargs):
        return Settings(**kwargs)

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
                .options(joinedload('simulations').joinedload('experiment').joinedload('analyzers')) \
                .order_by(Experiment.date_created.desc()).first()

            session.expunge_all()
        return experiment

    @classmethod
    def get_active_experiments(cls, location=None):
        with session_scope() as session:
            experiments = session.query(Experiment).distinct(Experiment.exp_id) \
                .join(Experiment.simulations) \
                .options(joinedload('simulations').joinedload('experiment').joinedload('analyzers')) \
                .filter(~Simulation.status.in_(('Succeeded', 'Failed', 'Canceled')))
            if location:
                experiments = experiments.filter(Experiment.location == location)

            experiments = experiments.all()
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
    def change_simulation_state(cls, sim, message=None, status=None, pid=None, session=None):
        with session_scope(session) as session:
            simulation = session.query(Simulation).filter(Simulation.id == sim.id).one()
            if message:
                simulation.message = message

            if status:
                simulation.status = status

            if pid:
                simulation.pid = pid if pid > 0 else None

    @classmethod
    def delete_experiments_by_suite(cls, suite_ids, verbose=False):
        """
        Delete those experiments which are associated with suite_ids
        suite_ids: list of suite ids
        """
        with session_scope() as session:
            # Issue: related tables are not deleted
            # num = session.query(Experiment).filter(Experiment.suite_id.in_(suite_ids)).delete(synchronize_session='fetch')

            # New approach: it will delete related simulations
            exps = session.query(Experiment).filter(Experiment.suite_id.in_(suite_ids))
            num = 0
            for exp in exps:
                session.delete(exp)
                num += 1
            if verbose:
                print '%s experiment(s) deleted.' % num

    @classmethod
    def clear_leftover(cls, suite_ids, exp_ids):
        """
        Delete those experiments which are associated with suite_id and not in exp_ids
        suite_ids: list of suite ids
        exp_ids: list of experiment ids
        """
        exp_orphan_list = cls.list_leftover(suite_ids, exp_ids)
        cls.delete_experiments(exp_orphan_list)

    @classmethod
    def list_leftover(cls, suite_ids, exp_ids):
        """
        List those experiments which are associated with suite_id and not in exp_ids
        suite_ids: list of suite ids
        exp_ids: list of experiment ids
        """
        exp_list = cls.get_experiments_by_suite(suite_ids)
        exp_list_ids = [exp.exp_id for exp in exp_list]

        # Calculate orphans
        exp_orphan_ids = list(set(exp_list_ids) - set(exp_ids))
        exp_orphan_list = [exp for exp in exp_list if exp.exp_id in exp_orphan_ids]

        return exp_orphan_list

    @classmethod
    def get_experiments_by_suite(cls, suite_ids):
        """
        Get the experiments which are associated with suite_id
        suite_ids: list of suite ids
        """
        exp_list = []
        with session_scope() as session:
            exp_list = session.query(Experiment).filter(Experiment.suite_id.in_(suite_ids)).all()
            session.expunge_all()

        return exp_list

    @classmethod
    def delete_experiments(cls, exp_list, verbose=False):
        """
        Delete experiments given from input
        exp_list: list of experiments
        """
        exp_ids = [exp.exp_id for exp in exp_list]
        with session_scope() as session:
            # Issue: related tables are not deleted
            # num = session.query(Experiment).filter(Experiment.exp_id.in_(exp_ids)).delete(synchronize_session='fetch')

            # New approach: it will delete related simulations
            exps = session.query(Experiment).filter(Experiment.exp_id.in_(exp_ids))
            num = 0
            for exp in exps:
                session.delete(exp)
                num += 1
            if verbose:
                print '%s experiment(s) deleted.' % num

    @classmethod
    def get_recent_experiment_by_filter(cls, num=20, is_all=False, name=None, location=None):
        with session_scope() as session:
            experiment = session.query(Experiment) \
                .options(joinedload('simulations')) \
                .order_by(Experiment.date_created.desc())

            if name:
                experiment = experiment.filter(Experiment.exp_name.like('%%%s%%' % name))

            if location:
                experiment = experiment.filter(Experiment.location == location)

            if is_all:
                experiment = experiment.all()
            else:
                experiment = experiment.limit(num).all()

            session.expunge_all()
        return experiment

